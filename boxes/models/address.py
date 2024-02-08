from django.db import models

class Address(models.Model):
    address = models.CharField(max_length=256)
    address2 = models.CharField(max_length=256, null=True)
    address3 = models.CharField(max_length=256, null=True)
    city = models.CharField(max_length=256)
    state_province = models.CharField(max_length=256)
    postal_code = models.CharField(max_length=16)
    country_code = models.CharField(max_length=3)
    instructions = models.CharField(max_length=4000, null=True)

class UserAddress(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    is_preferred = models.BooleanField()
