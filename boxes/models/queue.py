from django.db import models
from django.core.exceptions import ValidationError


class Queue(models.Model):
    description = models.TextField()
    check_in = models.BooleanField()


class PackageQueue(models.Model):
    package = models.OneToOneField("Package", on_delete=models.RESTRICT)
    queue = models.ForeignKey(Queue, on_delete=models.RESTRICT)


class PicklistQueue(models.Model):
    picklist = models.OneToOneField("Picklist", on_delete=models.RESTRICT)
    queue = models.OneToOneField(Queue, on_delete=models.RESTRICT)
