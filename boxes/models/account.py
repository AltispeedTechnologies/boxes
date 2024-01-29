from django.db import models

class Account(models.Model):
    user_id = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=8, decimal_places=2)
    is_good_standing = models.BooleanField()
    description = models.CharField(max_length=256, null=True)

class AccountLedger(models.Model):
    account_id = models.ForeignKey(Account, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=8, decimal_places=2)
    debit = models.DecimalField(max_digits=8, decimal_places=2)
    # This is intentionally NOT NULL -SQ
    description = models.CharField(max_length=256)

class UserAccount(models.Model):
    user_id = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account_id = models.ForeignKey(Account, on_delete=models.CASCADE)
