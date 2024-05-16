from django.db import models

PACKAGE_STATES = {
    (0, "Received"),
    (1, "Checked in"),
    (2, "Checked out"),
    (3, "Mis-placed"),
}

class PackageType(models.Model):
    shortcode = models.CharField(max_length=1)
    description = models.CharField(max_length=64)
    default_price = models.DecimalField(max_digits=8, decimal_places=2)


class Package(models.Model):
    account = models.ForeignKey("Account", on_delete=models.RESTRICT)
    carrier = models.ForeignKey("Carrier", on_delete=models.RESTRICT)
    package_type = models.ForeignKey(PackageType, on_delete=models.RESTRICT)
    inside = models.BooleanField(default=False)
    tracking_code = models.CharField(max_length=30, unique=True)
    current_state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES, default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    comments = models.CharField(max_length=256, null=True)


class PackageLedger(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.RESTRICT)
    package = models.ForeignKey(Package, on_delete=models.RESTRICT)
    state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES)
    timestamp = models.DateTimeField(auto_now_add=True)
