"""Authentication identity models: CustomUser and notification emails."""
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class CustomUser(AbstractUser):
    """Application user model (``AUTH_USER_MODEL``).

    Extends Django ``AbstractUser`` with warehouse profile fields. Role checks use **group membership** methods rather than only boolean flags.
    """
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
        """Return True if the user is in the Admin group."""
        return self.groups.filter(name="Admin").exists()

    def has_staff_role(self):
        """True if the user is in the Staff group.

        Named to avoid shadowing AbstractUser.is_staff (boolean field).
        """
        return self.groups.filter(name="Staff").exists()

    def is_customer(self):
        """Return True if the user is in the Customer group."""
        return self.groups.filter(name="Customer").exists()

    def has_delivery_role(self):
        """True if the user is in the Delivery group.

        Named like has_staff_role to avoid clashing with unrelated flags.
        """
        return self.groups.filter(name="Delivery").exists()


class CustomUserEmail(models.Model):
    """Notification email address for a login (Mailjet recipients).

    Distinct from ``AbstractUser.email``; users may have multiple notification addresses.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField(blank=False, max_length=254)
