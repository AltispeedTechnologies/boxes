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

    def is_staff(self):
        return self.groups.filter(name="Admin").exists() or self.groups.filter(name="Staff").exists()


class CustomUserEmail(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.RESTRICT)
    email = models.EmailField(blank=False, max_length=254)
