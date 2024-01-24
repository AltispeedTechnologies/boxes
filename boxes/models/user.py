from django.db import models
from .group import Group

class User(models.Model):
    group_id = models.ForeignKey(Group, on_delete=models.RESTRICT)
    email = models.CharField(max_length=256, unique=True)
    company = models.CharField(max_length=128, null=True)
    prefix = models.CharField(max_length=16, null=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    middle_name = models.CharField(max_length=64, null=True)
    suffix = models.CharField(max_length=16, null=True)
    comments = models.CharField(max_length=4000, null=True)
