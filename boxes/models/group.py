from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=32, unique=True)
    description = models.CharField(max_length=256)
