import json
import re
import stripe
from django.conf import settings
from boxes.management.exception_catcher import exception_catcher
from boxes.models import AccountStripeCustomer, UserAccount
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


@require_http_methods(["GET"])
def customer_payment_methods(request):
    customer_id = _get_customer_id(request.user.id)

    payment_methods = stripe.Customer.list_payment_methods(customer_id)
    print(customer_id)

    return render(request, "customer/payment_methods.html", {"payment_methods": payment_methods.data})


@require_http_methods(["GET"])
def customer_create_payment_method(request):
    customer_id = _get_customer_id(request.user.id)

    redirect_url = request.build_absolute_uri(reverse("customer_payment_methods"))

    stripe_session = stripe.checkout.Session.create(
        mode="setup",
        currency="usd",
        customer=customer_id,
        success_url=redirect_url,
        cancel_url=redirect_url,
    )

    return JsonResponse({"success": True, "url": stripe_session.url})
