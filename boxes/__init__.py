"""Boxes Django project package; loads Celery app for shared_task discovery."""
from .celery import app as celery_app

__all__ = ["celery_app"]
