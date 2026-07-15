"""Staging queues for check-in lines and picklist association."""
from django.db import models
from django.core.exceptions import ValidationError


class Queue(models.Model):
    """Named staging queue; ``check_in`` marks check-in line queues."""
    description = models.TextField()
    check_in = models.BooleanField()


class PackageQueue(models.Model):
    """Places a package into a queue (one queue membership per package)."""
    package = models.OneToOneField("Package", on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)


class PicklistQueue(models.Model):
    """Associates a picklist with a queue (one-to-one each side)."""
    picklist = models.OneToOneField("Picklist", on_delete=models.CASCADE)
    queue = models.OneToOneField(Queue, on_delete=models.CASCADE)
