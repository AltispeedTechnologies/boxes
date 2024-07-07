import json
import re
import stripe
from django.conf import settings
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Account, AccountBalance, AccountStripeCustomer, UserAccount
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_http_methods


# Set the stripe API key from our local configuration
stripe.api_key = settings.STRIPE_API_KEY


def _get_customer_id(user_id):
    account_id = UserAccount.objects.get(user_id=user_id).account_id
    _customer, _ = AccountStripeCustomer.objects.get_or_create(account_id=account_id)

    # If we are not storing a customer ID, create one
    if not _customer.customer_id:
        stripe_customer = stripe.Customer.create(metadata={"account_id": account_id})
        _customer.customer_id = stripe_customer["id"]
        _customer.save()
    # Verify the customer ID exists; if it has been deleted, re-create it
    else:
        stripe_customer = stripe.Customer.retrieve(_customer.customer_id)
        if "deleted" in stripe_customer and stripe_customer["deleted"]:
            stripe_customer = stripe.Customer.create(metadata={"account_id": account_id})
            _customer.customer_id = stripe_customer["id"]
            _customer.save()

    return _customer.customer_id


def _get_billing_portal_id():
    config_list = stripe.billing_portal.Configuration.list(limit=1)
    if len(config_list["data"]) == 0:
        billing_portal = stripe.billing_portal.Configuration.create(
            business_profile={
                "headline": "Boxes",
            },
            features={
                "customer_update": {"allowed_updates": ["name", "email"], "enabled": True},
                "invoice_history": {"enabled": False},
                "payment_method_update": {"enabled": True},
            },
        )
    else:
        billing_portal = config_list["data"][0]

    return billing_portal["id"]


@require_http_methods(["GET"])
def customer_make_payment(request):
    account_id = UserAccount.objects.get(user_id=request.user.id).account_id
    balance = Account.objects.get(pk=account_id).balance * -1
    other_balances = AccountBalance.objects.get(account_id=account_id)
    parcel_fees = other_balances.regular_balance * -1 if other_balances.regular_balance != 0.00 else None
    late_fees = other_balances.late_balance * -1 if other_balances.regular_balance != 0.00 else None

    return render(request, "customer/make_payment.html", {"balance": balance,
                                                          "parcel_fees": parcel_fees,
                                                          "late_fees": late_fees})


@require_http_methods(["GET"])
def customer_payment_methods(request):
    return render(request, "customer/_loading.html", {"view_type": "billing_portal"})


@require_http_methods(["GET"])
def customer_billing_portal(request):
    billing_portal_session = stripe.billing_portal.Session.create(
        customer=_get_customer_id(request.user.id),
        configuration=_get_billing_portal_id(),
        return_url=request.build_absolute_uri(reverse("home")),
    )
    customer_id = _get_customer_id(request.user.id)

    return JsonResponse({"success": True, "url": billing_portal_session["url"]})
