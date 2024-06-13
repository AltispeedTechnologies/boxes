from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField()
