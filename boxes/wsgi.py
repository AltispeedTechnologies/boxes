"""WSGI entrypoint for Gunicorn (``boxes.wsgi:application``)."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boxes.settings")
application = get_wsgi_application()
