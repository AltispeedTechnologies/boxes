"""Billing accounts, ledger, aliases, charge settings, and Stripe customer links."""
from django.db import models
from django.utils import timezone


class Account(models.Model):
    """Billing and parcel entity for a customer.

    ``user`` is the creator/owner (often staff), **not** the customer portal link — use ``UserAccount`` for that. Balance sign: negative typically means amount owed.
    """
    user = models.ForeignKey("CustomUser", on_delete=models.SET(1))
    name = models.CharField(max_length=64)
    balance = models.DecimalField(max_digits=8, decimal_places=2)
    billable = models.BooleanField()
    comments = models.CharField(max_length=256, null=True)

    def hr_balance(self):
        """Return a human-readable absolute dollar string for ``balance``."""
        positive_balance = self.balance * -1 if self.balance < 0 else self.balance
        balance = f"${positive_balance:.2f}"

        return balance

    def ensure_primary_alias(self):
        """Create or update the primary ``AccountAlias`` to match ``name``."""
        primary_alias = AccountAlias.objects.filter(account=self, primary=True).first()
        if primary_alias:
            primary_alias.alias = self.name
            primary_alias.save()
        else:
            primary_alias = AccountAlias(account=self, alias=self.name, primary=True)
            primary_alias.save()


# Exists to denormalize AccountLedger entries
class AccountBalance(models.Model):
    """Denormalized regular vs late balances for an account (1:1)."""
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    regular_balance = models.DecimalField(max_digits=8, decimal_places=2)
    late_balance = models.DecimalField(max_digits=8, decimal_places=2)

    def hr_regular_balance(self):
        """Human-readable regular balance string."""
        positive_regular_balance = self.regular_balance * -1 if self.regular_balance < 0 else self.regular_balance
        regular_balance = f"${positive_regular_balance:.2f}"

        return regular_balance

    def hr_late_balance(self):
        """Human-readable late balance string."""
        positive_late_balance = self.late_balance * -1 if self.late_balance < 0 else self.late_balance
        late_balance = f"${positive_late_balance:.2f}"

        return late_balance


class AccountLedger(models.Model):
    """Single financial movement (credit/debit) optionally tied to package or invoice."""
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=8, decimal_places=2)
    debit = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=256, null=True)
    package = models.ForeignKey("Package", on_delete=models.SET_NULL, null=True)
    invoice = models.ForeignKey("Invoice", on_delete=models.SET_NULL, null=True)
    is_late = models.BooleanField()


class UserAccount(models.Model):
    """Join table linking a login (CustomUser) to a billing Account for portal access."""
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)


class AccountAlias(models.Model):
    """Searchable alternate name for an account; one row may be ``primary``."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    alias = models.CharField(max_length=64)
    primary = models.BooleanField()


class AccountChargeSettings(models.Model):
    """Aging/storage fee rule applied by Celery ``age_charges``.

    Frequency codes: ``D`` daily, ``W`` weekly, ``M`` monthly.
    """
    FREQUENCY_CHOICES = (
        ("D", "Daily"),
        ("W", "Weekly"),
        ("M", "Monthly"),
    )

    days = models.IntegerField(null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    package_type = models.ForeignKey("PackageType", on_delete=models.CASCADE, null=True)
    frequency = models.CharField(max_length=1, choices=FREQUENCY_CHOICES, null=True)
    endpoint = models.IntegerField(null=True)


class AccountStripeCustomer(models.Model):
    """Stripe Customer id associated with an Account."""
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    customer_id = models.CharField(null=True)


class StripePaymentMethod(models.Model):
    """Cached Stripe payment method id for a customer."""
    customer = models.ForeignKey(AccountStripeCustomer, on_delete=models.CASCADE)
    payment_method_id = models.CharField()
