"""Singleton-style business configuration and branding images."""
from boxes.management.custom_storage import OverwriteStorage
from django.db import models


class GlobalSettings(models.Model):
    """Warehouse identity, tax/fee toggles, email master switch, and logos.

    Prefer GlobalSettings.load() over hard-coded primary keys. Edited via
    Management -> General. See docs/DATABASE_SETTINGS.md.
    """

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

    @classmethod
    def load(cls):
        """Return the singleton settings row, creating defaults if needed."""
        obj = cls.objects.order_by("pk").first()
        if obj is not None:
            return obj
        return cls.objects.create(
            name="Boxes",
            address1="",
            address2="",
            website="",
            email="",
            email_sending=True,
            taxes=False,
            pass_on_fees=False,
        )
