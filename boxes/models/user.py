from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    company = models.CharField(max_length=128, null=True)
    phone_number = models.CharField(max_length=20, null=True)
    mobile_number = models.CharField(max_length=20, null=True)
    prefix = models.CharField(max_length=16, null=True)
    middle_name = models.CharField(max_length=64, null=True)
    suffix = models.CharField(max_length=16, null=True)
    comments = models.CharField(max_length=4000, null=True)
    groups = models.ManyToManyField(Group, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions")

    def is_admin(self):
        return self.groups.filter(name="Admin").exists()

    def has_staff_role(self):
        """True if the user is in the Staff group.

        Named to avoid shadowing AbstractUser.is_staff (boolean field).
        """
        return self.groups.filter(name="Staff").exists()

    def is_customer(self):
        return self.groups.filter(name="Customer").exists()


class CustomUserEmail(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(blank=False, max_length=254)
