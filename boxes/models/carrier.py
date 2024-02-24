from django.db import models

class Carrier(models.Model):
    name = models.CharField(max_length=32, unique=True)
    phone_number = models.CharField(max_length=15)
    website = models.CharField(max_length=32)
