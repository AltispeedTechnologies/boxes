from django.db import models
from django.utils import timezone


class Account(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    balance = models.DecimalField(max_digits=8, decimal_places=2)
    billable = models.BooleanField()
    comments = models.CharField(max_length=256, null=True)

    def hr_balance(self):
        if self.balance >= 0:
            balance = f"${self.balance:.2f}"
        else:
            positive_balance = self.balance * -1
            balance = f"$({positive_balance:.2f})"

        return balance

    def ensure_primary_alias(self):
        primary_alias = AccountAlias.objects.filter(account=self, primary=True).first()
        if primary_alias:
            primary_alias.alias = self.name
            primary_alias.save()
        else:
            primary_alias = AccountAlias(account=self, alias=self.name, primary=True)
            primary_alias.save()


# Exists to denormalize AccountLedger entries
class AccountBalance(models.Model):
    account = models.OneToOneField(Account, on_delete=models.RESTRICT)
    regular_balance = models.DecimalField(max_digits=8, decimal_places=2)
    late_balance = models.DecimalField(max_digits=8, decimal_places=2)

    def hr_regular_balance(self):
        if self.regular_balance >= 0:
            regular_balance = f"${self.regular_balance:.2f}"
        else:
            positive_regular_balance = self.regular_balance * -1
            regular_balance = f"$({positive_regular_balance:.2f})"

        return regular_balance

    def hr_late_balance(self):
        if self.late_balance >= 0:
            late_balance = f"${self.late_balance:.2f}"
        else:
            positive_late_balance = self.late_balance * -1
            late_balance = f"$({positive_late_balance:.2f})"

        return late_balance


class AccountLedger(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=8, decimal_places=2)
    debit = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=256, null=True)
    package = models.ForeignKey("Package", on_delete=models.RESTRICT, null=True)
    is_late = models.BooleanField()


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


class AccountStripeCustomer(models.Model):
    account = models.ForeignKey(Account, on_delete=models.RESTRICT)
    customer_id = models.CharField(null=True)


class StripePaymentMethod(models.Model):
    customer = models.ForeignKey(AccountStripeCustomer, on_delete=models.RESTRICT)
    payment_method_id = models.CharField()
