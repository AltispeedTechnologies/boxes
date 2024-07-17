import json
import stripe
from boxes.models import AccountLedger, Invoice, Package
from boxes.tasks.charges import total_accounts
from celery import shared_task
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction


def process_successful_invoice(user_id, account_id, invoice_id, subtotal, line_items):
    # Separate regular and late fees
    regular_fees = sum(i["amt"] for i in line_items if not i["late"])
    late_fees = sum(i["amt"] for i in line_items if i["late"])

    # Packages paid for
    paid_ids = set(i["id"] for i in line_items if not i["prtl"] and i["id"])

    # Create new AccountLedger entries and update the packages to be marked as paid
    with transaction.atomic():
        if regular_fees > 0:
            AccountLedger.objects.create(user_id=user_id, account_id=account_id, credit=Decimal(regular_fees),
                                         debit=0, invoice_id=invoice_id, is_late=False)

        if late_fees > 0:
            AccountLedger.objects.create(user_id=user_id, account_id=account_id, credit=Decimal(late_fees),
                                         debit=0, invoice_id=invoice_id, is_late=True)

        Package.objects.filter(pk__in=paid_ids).update(paid=True)

    total_accounts.delay(account_id=account_id)


@shared_task
def handle_stripe_webhook(payment_intent, user_id):
    invoice = Invoice.objects.filter(payment_intent_id=payment_intent["id"]).first()
    if not invoice:
        return

    match payment_intent["status"]:
        case "succeeded":
            process_successful_invoice(invoice.user_id, invoice.account_id, invoice.id, invoice.subtotal,
                                       invoice.line_items)
            invoice.current_state = 3
        case "requires_payment_method":
            invoice.current_state = 4
        case "canceled":
            Invoice.objects.filter(pk=invoice.id).delete()
            invoice = None

    if invoice:
        invoice.save()


@shared_task
def remove_old_coupons():
    day_ago_epoch = (datetime.now() - timedelta(days=1)).strftime("%s")
    coupon_ids = []
    coupons = stripe.Coupon.list(created={"lte": day_ago_epoch})

    while coupons["has_more"] or len(coupons["data"]) > 0:
        coupon_ids.extend(coupon["id"] for coupon in coupons["data"])
        coupons = stripe.Coupon.list(created={"lte": day_ago_epoch}, starting_after=coupon_ids[-1])

    for coupon_id in coupon_ids:
        stripe.Coupon.delete(coupon_id)
