from boxes.management.custom_storage import OverwriteStorage
from django.db import models
from django.utils import timezone


class GlobalSettings(models.Model):
    # General business information, for labels and invoices
    name = models.CharField(max_length=32)
    address1 = models.CharField(max_length=64)
    address2 = models.CharField(max_length=64)
    website = models.CharField(max_length=64)
    email = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=20, null=True)

    # Toggle email sending
    email_sending = models.BooleanField(default=True)

    # Invoice settings
    taxes = models.BooleanField(default=False)
    tax_rate = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    tax_stripe_id = models.CharField(max_length=30, null=True)
    pass_on_fees = models.BooleanField(default=False)

    # Logos, converted from the source image
    source_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    login_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    label_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    navbar_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
    favicon_image = models.ImageField(storage=OverwriteStorage(), upload_to="images/")
