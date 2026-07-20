"""Management command: populate demo data."""
from django.core.management.base import BaseCommand

from boxes.tasks import populate_seed_data


class Command(BaseCommand):
    """Run ``populate_seed_data`` synchronously or via Celery."""

    help = (
        "Populate development seed data. Use --sync to run in-process "
        "(no Celery worker required); default enqueues a Celery task."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Run seed population synchronously instead of Celery .delay()",
        )
        parser.add_argument(
            "--accounts",
            type=int,
            default=None,
            help="Override number of fake accounts (default task size)",
        )
        parser.add_argument(
            "--packages",
            type=int,
            default=None,
            help="Override number of fake packages (default task size)",
        )

    def handle(self, *args, **options):
        kwargs = {}
        if options.get("accounts") is not None:
            kwargs["account_count"] = options["accounts"]
        if options.get("packages") is not None:
            kwargs["package_count"] = options["packages"]

        if options["sync"]:
            self.stdout.write("Running populate_seed_data synchronously...")
            populate_seed_data(**kwargs)
            self.stdout.write(self.style.SUCCESS("Seed data loaded."))
        else:
            populate_seed_data.delay(**kwargs)
            self.stdout.write(self.style.SUCCESS("Seed data task enqueued."))
