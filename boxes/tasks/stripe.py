"""Stripe webhook processing, invoice settlement, and coupon cleanup."""
import stripe
from boxes.models import AccountLedger, Invoice, Package
from boxes.tasks.charges import total_accounts
from celery import shared_task
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone


def process_successful_invoice(user_id, account_id, invoice_id, subtotal, line_items):
    """Apply successful payment to ledger and mark packages paid.

    Not idempotent by itself — callers must use :func:`apply_invoice_success`
    so duplicate webhooks / UI refresh do not double-credit the ledger.
    """
    regular_fees = sum(i["amt"] for i in line_items if not i["late"])
    late_fees = sum(i["amt"] for i in line_items if i["late"])
    paid_ids = set(i["id"] for i in line_items if not i.get("prtl") and i.get("id"))

    with transaction.atomic():
        if regular_fees > 0:
            AccountLedger.objects.create(
                user_id=user_id,
                account_id=account_id,
                credit=Decimal(str(regular_fees)),
                debit=0,
                invoice_id=invoice_id,
                is_late=False,
            )

        if late_fees > 0:
            AccountLedger.objects.create(
                user_id=user_id,
                account_id=account_id,
                credit=Decimal(str(late_fees)),
                debit=0,
                invoice_id=invoice_id,
                is_late=True,
            )

        if paid_ids:
            Package.objects.filter(pk__in=paid_ids).update(paid=True)

    total_accounts.delay(account_id=account_id)


def apply_invoice_success(invoice):
    """Idempotently settle an invoice after Stripe reports success.

    Returns ``True`` if ledger/package updates were applied now, ``False`` if
    this invoice was already settled (safe for webhook retries and UI refresh).
    """
    with transaction.atomic():
        inv = Invoice.objects.select_for_update().select_related().get(pk=invoice.pk)
        already = AccountLedger.objects.filter(invoice_id=inv.pk).exists()
        if already:
            if inv.current_state != 3:
                inv.current_state = 3
                inv.save(update_fields=["current_state"])
            return False

        process_successful_invoice(
            inv.user_id,
            inv.account_id,
            inv.id,
            inv.subtotal,
            inv.line_items or [],
        )
        inv.current_state = 3
        inv.save(update_fields=["current_state"])
        return True


def sync_invoice_from_payment_intent(invoice, payment_intent):
    """Update invoice state from a PaymentIntent dict/object; settle on success.

    ``payment_intent`` may be a Stripe object or a plain dict with ``status``
    and ``id``. Returns the updated invoice (or ``None`` if deleted on cancel).
    """
    if hasattr(payment_intent, "to_dict_recursive"):
        payment_intent = payment_intent.to_dict_recursive()
    elif hasattr(payment_intent, "to_dict"):
        payment_intent = payment_intent.to_dict()

    status = payment_intent.get("status") if isinstance(payment_intent, dict) else None
    if status is None:
        return invoice

    match status:
        case "succeeded":
            apply_invoice_success(invoice)
            invoice.refresh_from_db()
        case "processing":
            if invoice.current_state not in (3,):
                invoice.current_state = 2
                invoice.save(update_fields=["current_state"])
        case "requires_action":
            if invoice.current_state not in (3,):
                invoice.current_state = 1
                invoice.save(update_fields=["current_state"])
        case "requires_payment_method":
            if invoice.current_state not in (3,):
                invoice.current_state = 4
                invoice.save(update_fields=["current_state"])
        case "canceled":
            # Only drop unpaid invoices that never settled
            if invoice.current_state != 3 and not AccountLedger.objects.filter(
                invoice_id=invoice.pk
            ).exists():
                Invoice.objects.filter(pk=invoice.pk).delete()
                return None
        case _:
            pass
    return invoice


@shared_task
def handle_stripe_webhook(payment_intent, user_id=None):
    """Celery task: process a PaymentIntent event.

    ``user_id`` is accepted for backward compatibility but ignored; the
    Invoice row supplies user/account ids on success.
    """
    if not isinstance(payment_intent, dict):
        if hasattr(payment_intent, "to_dict_recursive"):
            payment_intent = payment_intent.to_dict_recursive()
        elif hasattr(payment_intent, "to_dict"):
            payment_intent = payment_intent.to_dict()
        else:
            return

    pi_id = payment_intent.get("id")
    if not pi_id:
        return

    invoice = Invoice.objects.filter(payment_intent_id=pi_id).first()
    if not invoice:
        return

    sync_invoice_from_payment_intent(invoice, payment_intent)


@shared_task
def remove_old_coupons():
    """Celery beat: delete expired Stripe coupons."""
    day_ago_epoch = str(int((timezone.now() - timedelta(days=1)).timestamp()))
    coupon_ids = []
    coupons = stripe.Coupon.list(created={"lte": day_ago_epoch})

    while coupons["has_more"] or len(coupons["data"]) > 0:
        coupon_ids.extend(coupon["id"] for coupon in coupons["data"])
        coupons = stripe.Coupon.list(
            created={"lte": day_ago_epoch}, starting_after=coupon_ids[-1]
        )

    for coupon_id in coupon_ids:
        stripe.Coupon.delete(coupon_id)
