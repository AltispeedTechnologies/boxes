from django.db import models
from django.core.exceptions import ValidationError

class Queue(models.Model):
    description = models.TextField()
    check_in = models.BooleanField()

class PackageQueue(models.Model):
    package = models.OneToOneField("Package", on_delete=models.RESTRICT)
    queue = models.ForeignKey(Queue, on_delete=models.RESTRICT)
