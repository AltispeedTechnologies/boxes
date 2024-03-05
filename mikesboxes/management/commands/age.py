from django.core.management.base import BaseCommand
from boxes.models import Package, AccountLedger

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        # Your cleanup logic goes here
        Package.objects.filter()
        self.stdout.write(self.style.SUCCESS('Cleanup completed successfully'))
