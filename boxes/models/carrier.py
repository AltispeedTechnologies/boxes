"""Delivery carrier catalog."""
from django.db import models


class Carrier(models.Model):
    """Shipping carrier (name, phone, website) selectable on packages."""
    name = models.CharField(max_length=32, unique=True)
    phone_number = models.CharField(max_length=15)
    website = models.CharField(max_length=32)
    is_active = models.BooleanField(default=True)
    allow_duplicate_tracking = models.BooleanField(default=False)
