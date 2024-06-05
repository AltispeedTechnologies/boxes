from boxes.management.custom_storage import OverwriteStorage
from django.db import models
from django.utils import timezone


class GlobalSettings(models.Model):
    name = models.CharField(max_length=32)
    address1 = models.CharField(max_length=64)
    address2 = models.CharField(max_length=64)
    website = models.CharField(max_length=64)
    email = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=20, null=True)
    source_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    login_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    label_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    navbar_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    favicon_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
