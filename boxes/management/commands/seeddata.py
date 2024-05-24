from boxes.tasks import populate_seed_data
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        populate_seed_data.delay()
