import os
import re
from collections import defaultdict
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Runs collectstatic and cleans up old files"

    def handle(self, *args, **options):
        self.stdout.write("Running collectstatic")
        call_command("collectstatic", interactive=False)
        self.stdout.write("collectstatic complete")

        source_directory = os.path.join(settings.BASE_DIR, "boxes/static/js")
        target_directory = os.path.join(settings.STATIC_ROOT, "js")

        checksum_pattern = re.compile(r'^(.*)\.([a-f0-9]{12})\.js$')

        files_dict = defaultdict(list)

        # Collect files from target_directory
        self.stdout.write("Collecting files")
        for root, _, files in os.walk(target_directory):
            for file in files:
                if file.endswith(".js"):
                    full_path = os.path.join(root, file)
                    match = checksum_pattern.match(file)
                    base_name = match.group(1) if match else file
                    files_dict[base_name].append(full_path)

        # Determine which files to keep and which to remove
        self.stdout.write("Processing files")
        for base_name, file_list in files_dict.items():
            if settings.DEBUG:
                # Keep only non-checksummed files in DEBUG mode
                non_checksum_files = [f for f in file_list if not checksum_pattern.match(os.path.basename(f))]
                for file_path in file_list:
                    if file_path not in non_checksum_files:
                        os.remove(file_path)
            else:
                # Keep only the most recent checksummed file in non-DEBUG mode
                checksum_files = [f for f in file_list if checksum_pattern.match(os.path.basename(f))]
                if checksum_files:
                    checksum_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
                    most_recent_file = checksum_files[0]
                    for file_path in checksum_files[1:]:
                        os.remove(file_path)
                    for file_path in file_list:
                        if file_path not in checksum_files:
                            os.remove(file_path)
                else:
                    for file_path in file_list:
                        os.remove(file_path)

        # Synchronize deletions from source_directory to target_directory
        self.stdout.write("Synchronizing deletions")
        source_files = {f for f in os.listdir(source_directory) if f.endswith(".js")}
        for target_file in os.listdir(target_directory):
            if target_file.endswith(".js"):
                base_name_match = checksum_pattern.match(target_file)
                base_name = base_name_match.group(1) + ".js" if base_name_match else target_file

                if base_name not in source_files:
                    target_path = os.path.join(target_directory, target_file)
                    os.remove(target_path)

        self.stdout.write("Completed successfully")
