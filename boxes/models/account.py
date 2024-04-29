from django.db import models

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

class AccountLedger(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=8, decimal_places=2)
    debit = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=256, null=True)
    package = models.ForeignKey("Package", on_delete=models.RESTRICT, null=True)

class UserAccount(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
