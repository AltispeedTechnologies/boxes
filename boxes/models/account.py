from django.db import models
from django.utils import timezone

class Account(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    balance = models.DecimalField(max_digits=8, decimal_places=2)
    is_good_standing = models.BooleanField()
    comments = models.CharField(max_length=256, null=True)

    def hr_balance(self):
        if self.balance >= 0:
            balance = f"${self.balance:.2f}"
        else:
            positive_balance = self.balance * -1
            balance = f"$({positive_balance:.2f})"

        return balance

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Ensure there is a primary alias for this account or update it
        self.ensure_primary_alias()

    def ensure_primary_alias(self):
        primary_alias = AccountAlias.objects.filter(account=self, primary=True).first()
        if primary_alias:
            primary_alias.alias = self.name
            primary_alias.save()
        else:
            primary_alias = AccountAlias(account=self, alias=self.name, primary=True)
            primary_alias.save()

class AccountLedger(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=8, decimal_places=2)
    debit = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=256, null=True)
    package = models.ForeignKey("Package", on_delete=models.RESTRICT, null=True)

class UserAccount(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.RESTRICT)
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)

class AccountAlias(models.Model):
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)
    alias = models.CharField(max_length=64)
    primary = models.BooleanField()

class AccountChargeSettings(models.Model):
    FREQUENCY_CHOICES = (
        ("D", "Daily"),
        ("W", "Weekly"),
        ("M", "Monthly"),
    )

    days = models.IntegerField(null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    package_type = models.ForeignKey("PackageType", on_delete=models.RESTRICT, null=True)
    frequency = models.CharField(max_length=1, choices=FREQUENCY_CHOICES, null=True)
    endpoint = models.IntegerField(null=True)
