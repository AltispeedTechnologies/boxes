from django.db import models

class Package(models.Model):
    account_id = models.ForeignKey("Account", on_delete=models.CASCADE)
    address_id = models.ForeignKey(Address, on_delete=models.CASCADE)
    tracking_code = models.CharField(max_length=30, unique=True)
    current_state = models.CharField(max_length=1)

class PackageLedger(models.Model):
    user_id = models.ForeignKey("User", on_delete=models.RESTRICT)
    package_id = models.ForeignKey(Package, on_delete=models.CASCADE)
    new_state = models.CharField(max_length=1)
    timestamp = models.DateTimeField(auto_now_add=True)
