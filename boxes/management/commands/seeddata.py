"""Management command: queue demo data population."""
from boxes.tasks import populate_seed_data
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Enqueue ``populate_seed_data`` Celery task."""
    help = ""

    def handle(self, *args, **options):
        """Call ``populate_seed_data.delay()``."""
        populate_seed_data.delay()
