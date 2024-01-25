from django.contrib.auth.models import User as DefaultUser
from django.db import models
from .group import Group

class User(DefaultUser):
    company = models.CharField(max_length=128, null=True)
    prefix = models.CharField(max_length=16, null=True)
    middle_name = models.CharField(max_length=64, null=True)
    suffix = models.CharField(max_length=16, null=True)
    comments = models.CharField(max_length=4000, null=True)
