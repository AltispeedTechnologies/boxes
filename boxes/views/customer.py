import json
import stripe
from boxes.backend import invoice
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Account, AccountLedger, Invoice, Package, StripePaymentMethod, UserAccount
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Case, DecimalField, F, OuterRef, Max, Subquery, Sum, When, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.http import require_http_methods


# Set the stripe API key from our local configuration
stripe.api_key = settings.STRIPE_API_KEY


@require_http_methods(["GET"])
def customer_make_payment(request):
    account_id = UserAccount.objects.get(user_id=request.user.id).account_id

    subtotal = float(Account.objects.get(pk=account_id).balance * -1)
    tax = round(subtotal * 0.075, 2)
    total = subtotal + tax
    balance = {"subtotal": subtotal, "tax": tax, "total": total}

    payment_methods, default_method = invoice.get_payment_methods(request.user.id)
    line_items = invoice.generate_line_items(subtotal, request.user.id)
    invoice_payload = {"line_items": line_items, "balance": balance}

    return render(request, "customer/make_payment.html", {"invoice": invoice_payload,
                                                          "payment_methods": payment_methods,
                                                          "default_payment_method": default_method})


@require_http_methods(["GET"])
def customer_payment_methods(request):
    return render(request, "customer/_loading.html", {"view_type": "billing_portal"})


@require_http_methods(["GET"])
def customer_billing_portal(request):
    billing_portal_session = stripe.billing_portal.Session.create(
        customer=invoice.get_customer_id(request.user.id),
        configuration=invoice.get_billing_portal_id(),
        return_url=request.build_absolute_uri(reverse("home")),
    )
    customer_id = invoice.get_customer_id(request.user.id)

    return JsonResponse({"success": True, "url": billing_portal_session["url"]})


@require_http_methods(["GET"])
def customer_view_invoice(request, pk):
    invoice_data = Invoice.objects.get(pk=pk)

    payment_intent = None
    session_id = request.GET.get("session_id", None)
    if session_id and invoice_data.current_state == 0:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        if checkout_session["mode"] == "setup":
            setup_intent = stripe.SetupIntent.retrieve(checkout_session["setup_intent"])
            payment_method = setup_intent["payment_method"]
            amount = round((invoice_data.subtotal + invoice_data.tax) * 100)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                payment_method=payment_method,
                customer=invoice.get_customer_id(request.user.id),
                currency="usd"
            )
            invoice_data.payment_intent_id = payment_intent.id
        elif checkout_session["mode"] == "payment":
            invoice_data.payment_intent_id = checkout_session["payment_intent"]
            if checkout_session["payment_status"] == "paid":
                invoice_data.current_state = 3
            elif checkout_session["payment_status"] == "unpaid":
                invoice_data.current_state = 2
    elif invoice_data.current_state == 1:
        payment_intent = stripe.PaymentIntent.retrieve(invoice_data.payment_intent_id)
        match payment_intent["status"]:
            case "requires_action":
                invoice_data.current_state = 1
            case "processing":
                invoice_data.current_state = 2
            case "succeeded":
                invoice_data.current_state = 3
            case "requires_payment_method":
                invoice_data.current_state = 4

    invoice_data.save()

    if not payment_intent:
        payment_intent = stripe.PaymentIntent.retrieve(invoice_data.payment_intent_id)

    payment_method = payment_intent["payment_method"]
    if not payment_method and payment_intent["last_payment_error"]:
        if payment_intent["last_payment_error"]["payment_method"]:
            payment_method = payment_intent["last_payment_error"]["payment_method"]["id"]

    if payment_method:
        payment_method = stripe.PaymentMethod.retrieve(payment_method)
        payment_method = invoice.get_payment_method_json(payment_method, None)

    total = invoice_data.subtotal + invoice_data.tax
    balance = {"subtotal": invoice_data.subtotal, "tax": invoice_data.tax, "total": total}
    invoice_payload = {"balance": balance, "current_state": invoice_data.current_state, "id": invoice_data.id,
                       "line_items": invoice_data.line_items, "payment_method": payment_method}

    return render(request, "customer/view_invoice.html", {"invoice": invoice_payload})


@require_http_methods(["GET"])
def customer_cancel_invoice(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    if invoice.current_state in [0, 1, 4]:
        if invoice.payment_intent_id:
            stripe.PaymentIntent.cancel(invoice.payment_intent_id)

    return redirect(reverse("customer_make_payment"))


@require_http_methods(["GET"])
def customer_parcels(request):
    account_id = UserAccount.objects.get(user_id=request.user.id).account_id

    packages = Package.objects.select_related(
        "carrier", "packagetype", "packagepicklist"
    ).annotate(
        check_in_time=Max(Case(
            When(packageledger__state=1, then="packageledger__timestamp")
        )),
        check_out_time=Max(Case(
            When(packageledger__state=2, then="packageledger__timestamp")
        )),
        cost=F("price"),
        picklist_id=F("packagepicklist__picklist_id"),
        picklist_date=F("packagepicklist__picklist__date")
    ).values(
        "id",
        "picklist_id",
        "carrier_id",
        "package_type_id",
        "current_state",
        "paid",
        "cost",
        "carrier__name",
        "package_type__description",
        "picklist_date",
        "tracking_code",
        "check_in_time",
        "check_out_time"
    ).filter(account_id=account_id).order_by("current_state", "-check_in_time")

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(packages, per_page)
    page_obj = paginator.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []

    return render(request, "customer/parcels.html", {"page_obj": page_obj,
                                                     "selected": selected})


@require_http_methods(["POST"])
@exception_catcher()
def customer_confirm_invoice(request, pk):
    invoice_data = Invoice.objects.get(pk=pk)
    invoice_url = request.build_absolute_uri(reverse("customer_view_invoice", kwargs={"pk": invoice_data.id}))

    if invoice_data.current_state == 4:
        payment_intent = stripe.PaymentIntent.retrieve(invoice_data.payment_intent_id)
        if payment_intent["last_payment_error"] and payment_intent["last_payment_error"]["payment_method"]:
            payment_method = payment_intent["last_payment_error"]["payment_method"]["id"]
            payment_intent = stripe.PaymentIntent.modify(invoice_data.payment_intent_id, payment_method=payment_method)

    try:
        payment_intent = stripe.PaymentIntent.confirm(invoice_data.payment_intent_id, return_url=invoice_url)
    except stripe.error.InvalidRequestError as e:
        if "already succeeded" in str(e):
            invoice_data.current_state = 3
            invoice_data.save()
            return JsonResponse({"success": True, "url": None})

    redirect_url = None
    match payment_intent["status"]:
        case "requires_action":
            invoice_data.current_state = 1
            if payment_intent["next_action"]["type"] == "redirect_to_url":
                redirect_url = payment_intent["next_action"]["redirect_to_url"]["url"]
        case "processing":
            invoice_data.current_state = 2
        case "succeeded":
            invoice_data.current_state = 3
        case "requires_payment_method":
            invoice_data.current_state = 4

    invoice_data.save()
    return JsonResponse({"success": True, "url": redirect_url})


@require_http_methods(["POST"])
@exception_catcher()
def customer_new_invoice(request):
    account_id = UserAccount.objects.get(user_id=request.user.id).account_id
    customer_id = invoice.get_customer_id(request.user.id)

    data = json.loads(request.body)
    method = data["method"]

    subtotal = float(data["amount"])
    if subtotal < 0.50:
        raise ValueError
    line_items = invoice.generate_line_items(subtotal, request.user.id)

    tax = round(subtotal * 0.075, 2)
    total = round((subtotal + tax) * 100)

    payment_intent_id, url = None, None
    if method not in ["ONETIME", "NEW"]:
        payment_method = StripePaymentMethod.objects.filter(pk=method, customer__customer_id=customer_id).first()
        if not payment_method:
            raise ValueError

        payment_intent = stripe.PaymentIntent.create(
            amount=total,
            payment_method=payment_method.payment_method_id,
            customer=customer_id,
            currency="usd"
        )
        payment_intent_id = payment_intent.id

    invoice_data = Invoice.objects.create(account_id=account_id, user_id=request.user.id,
                                          payment_intent_id=payment_intent_id, line_items=line_items,
                                          subtotal=subtotal, tax=tax)
    invoice_url = request.build_absolute_uri(reverse("customer_view_invoice", kwargs={"pk": invoice_data.id}))
    success_url = invoice_url + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = f"{invoice_url}/cancel"

    if method == "ONETIME":
        line_items, discount = invoice.generate_checkout_line_items(line_items)

        if discount:
            coupon = stripe.Coupon.create(amount_off=discount, currency="usd", name="Account Credit")
            discount = [{"coupon": coupon["id"]}]

        checkout_session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=line_items,
            discounts=discount if discount else [],
            mode="payment",
            ui_mode="hosted"
        )

        url = checkout_session["url"]
    elif method == "NEW":
        checkout_session = stripe.checkout.Session.create(
            mode="setup",
            currency="usd",
            customer=customer_id,
            success_url=success_url,
            cancel_url=cancel_url
        )
        url = checkout_session["url"]

    if not url:
        url = invoice_url

    return JsonResponse({"success": True, "url": url})
