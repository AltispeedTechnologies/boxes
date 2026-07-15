"""Staff Stripe payment totals summary (succeeded invoices)."""
from decimal import Decimal

from boxes.models import Invoice
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def stripe_totals(request):
    """GET: aggregate succeeded invoice money fields for staff reports."""
    agg = Invoice.objects.filter(current_state=3).aggregate(
        count=Count("id"),
        subtotal=Coalesce(Sum("subtotal"), Decimal("0.00")),
        tax=Coalesce(Sum("tax"), Decimal("0.00")),
        processing_fees=Coalesce(Sum("processing_fees"), Decimal("0.00")),
        stripe_fee=Coalesce(Sum("stripe_fee"), Decimal("0.00")),
        deposit_total=Coalesce(Sum("deposit_total"), Decimal("0.00")),
    )
    return render(request, "reports/stripe_totals.html", {"totals": agg})
