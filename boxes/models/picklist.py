"""Pickup lists grouping packages for batch checkout."""
from django.db import models
from django.core.exceptions import ValidationError


class Picklist(models.Model):
    """A named/dated list of packages to pull for pickup.

    Requires at least one of ``date`` or ``description``.
    """
    date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def clean(self):
        """Validate that date or description is present."""
        if not self.date and not self.description:
            raise ValidationError("At least one of timestamp or description must be provided.")

    def save(self, *args, **kwargs):
        """Run validation then save."""
        self.clean()
        super().save(*args, **kwargs)


class PackagePicklist(models.Model):
    """Membership of a package on a picklist (one picklist per package)."""
    package = models.OneToOneField("Package", on_delete=models.CASCADE)
    picklist = models.ForeignKey(Picklist, on_delete=models.CASCADE)
