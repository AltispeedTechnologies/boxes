from django.db import models


PAYMENT_INTENT_STATES = [
    (0, "Created"),
    (1, "Requires Action"),
    (2, "Processing"),
    (3, "Succeeded"),
    (4, "Failed"),
]


class Invoice(models.Model):
    account = models.ForeignKey("Account", on_delete=models.RESTRICT)
    user = models.ForeignKey("CustomUser", on_delete=models.RESTRICT)
    timestamp = models.DateTimeField(auto_now_add=True)

    payment_intent_id = models.CharField(null=True)
    current_state = models.PositiveSmallIntegerField(choices=PAYMENT_INTENT_STATES, default=0)

    line_items = models.JSONField()
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)
    tax = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    processing_fees = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    stripe_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    deposit_total = models.DecimalField(max_digits=8, decimal_places=2, null=True)
