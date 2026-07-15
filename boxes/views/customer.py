"""Customer portal: parcels, payments, invoices, billing portal, membership."""
from django.utils import timezone
import json
import stripe
from boxes.backend import invoice
from boxes.backend.membership import (
    get_active_account,
    list_accounts_for_user,
    require_account_member,
    set_active_account,
)
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Account, AccountLedger, GlobalSettings, Invoice, Package, StripePaymentMethod
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Case, F, Max, When
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from weasyprint import HTML


def _customer_account_or_response(request, *, for_json=False):
    """Resolve active account or return a select/empty-state response.

    Returns ``(account, None)`` when resolved, or ``(None, HttpResponse)`` when
    the caller should return the response as-is.
    """
    account = get_active_account(request)
    if account is not None:
        return account, None

    accounts = list(list_accounts_for_user(request.user))
    if for_json:
        if not accounts:
            return None, JsonResponse(
                {"success": False, "errors": ["No linked accounts."]},
                status=400,
            )
        return None, JsonResponse(
            {
                "success": False,
                "errors": ["Select an account first."],
                "redirect": reverse("customer_select_account"),
            },
            status=400,
        )

    if not accounts:
        return None, render(request, "customer/no_account.html")
    return None, render(
        request,
        "customer/select_account.html",
        {
            "accounts": accounts,
            "next": request.get_full_path(),
        },
    )


def _invoice_for_member(request, pk):
    """Load invoice and ensure the user is an active member of its account."""
    invoice_data = Invoice.objects.select_related("account").get(pk=pk)
    require_account_member(request.user, invoice_data.account)
    return invoice_data


@require_http_methods(["GET", "POST"])
def customer_select_account(request):
    """GET: list linked accounts. POST: set active account in session."""
    accounts = list(list_accounts_for_user(request.user))
    if not accounts:
        return render(request, "customer/no_account.html")

    if request.method == "POST":
        account_id = request.POST.get("account_id")
        if not account_id and request.body:
            try:
                account_id = json.loads(request.body).get("account_id")
            except json.JSONDecodeError:
                account_id = None
        if account_id is None:
            return JsonResponse({"success": False, "errors": ["account_id is required"]}, status=400)
        try:
            set_active_account(request, int(account_id))
        except PermissionDenied:
            return HttpResponseForbidden("Not an active member of this account.")
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")
        wants_json = (
            "application/json" in request.headers.get("Accept", "")
            or request.content_type == "application/json"
        )
        if wants_json:
            return JsonResponse({"success": True, "redirect": next_url})
        return redirect(next_url)

    active = get_active_account(request)
    return render(
        request,
        "customer/select_account.html",
        {
            "accounts": accounts,
            "active_account": active,
            "next": request.GET.get("next", reverse("home")),
        },
    )


@require_http_methods(["POST"])
@exception_catcher()
def session_set_active_account(request):
    """POST: set session active account after membership check."""
    data = json.loads(request.body) if request.body else {}
    account_id = data.get("account_id") or request.POST.get("account_id")
    if account_id is None:
        raise ValueError("account_id is required")
    account = set_active_account(request, int(account_id))
    next_url = data.get("next") or request.POST.get("next") or reverse("home")
    return JsonResponse({"success": True, "account_id": account.id, "redirect": next_url})


@require_http_methods(["GET"])
def customer_make_payment(request):
    """GET: payment page with balance and methods."""
    account, early = _customer_account_or_response(request)
    if early:
        return early
    account_id = account.id
    globalsettings = GlobalSettings.load()

    subtotal = float(Account.objects.get(pk=account_id).amount_owed())
    tax_rate = float(globalsettings.tax_rate / 100) if globalsettings.taxes else 0.00
    tax = round(subtotal * tax_rate, 2)
    total = subtotal + tax

    processing_fees = None
    if globalsettings.pass_on_fees:
        processing_fees = ((total * 0.029) + 0.30)
        cur_proc_fees = processing_fees * 0.029
        while round(cur_proc_fees, 2) >= 0.01:
            processing_fees += cur_proc_fees
            cur_proc_fees = cur_proc_fees * 0.029

        total += round(processing_fees, 2)

    balance = {
        "subtotal": subtotal,
        "tax": tax,
        "tax_rate": tax_rate * 100,
        "total": total,
        "processing_fees": processing_fees,
    }

    payment_methods, default_method = invoice.get_payment_methods(account_id)
    line_items = invoice.generate_line_items(subtotal, account_id)
    invoice_payload = {"line_items": line_items, "balance": balance}

    return render(
        request,
        "customer/make_payment.html",
        {
            "invoice": invoice_payload,
            "payment_methods": payment_methods,
            "default_payment_method": default_method,
            "active_account": account,
        },
    )


@require_http_methods(["GET"])
def customer_payment_methods(request):
    """GET: payment methods data for UI."""
    account, early = _customer_account_or_response(request)
    if early:
        return early
    return render(
        request,
        "customer/_loading.html",
        {"view_type": "billing_portal", "active_account": account},
    )


@require_http_methods(["GET"])
def customer_billing_portal(request):
    """GET: redirect to Stripe Billing Portal session."""
    account, early = _customer_account_or_response(request, for_json=True)
    if early:
        return early
    billing_portal_session = stripe.billing_portal.Session.create(
        customer=invoice.get_customer_id(account.id),
        configuration=invoice.get_billing_portal_id(),
        return_url=request.build_absolute_uri(reverse("home")),
    )
    return JsonResponse({"success": True, "url": billing_portal_session["url"]})


@require_http_methods(["GET"])
def customer_view_invoice(request, pk):
    """GET: invoice detail / confirmation page."""
    try:
        invoice_data = _invoice_for_member(request, pk)
    except PermissionDenied:
        return HttpResponseForbidden()
    except Invoice.DoesNotExist:
        return HttpResponseForbidden()

    payment_intent = None
    session_id = request.GET.get("session_id", None)
    if session_id and invoice_data.current_state == 0:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        if checkout_session["mode"] == "setup":
            setup_intent = stripe.SetupIntent.retrieve(checkout_session["setup_intent"])
            payment_method = setup_intent["payment_method"]
            prelim_amount = invoice_data.subtotal + invoice_data.tax if invoice_data.tax else invoice_data.subtotal
            amount = round(prelim_amount * 100)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                payment_method=payment_method,
                customer=invoice.get_customer_id(invoice_data.account_id),
                currency="usd",
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

    if invoice_data.tax and invoice_data.tax > 0:
        total = invoice_data.subtotal + invoice_data.tax
        tax_rate = ((invoice_data.tax / invoice_data.subtotal) * 100)
    else:
        total = invoice_data.subtotal
        tax_rate = None

    if invoice_data.processing_fees:
        total += invoice_data.processing_fees
    balance = {
        "subtotal": invoice_data.subtotal,
        "tax": invoice_data.tax,
        "tax_rate": tax_rate,
        "total": total,
        "processing_fees": invoice_data.processing_fees,
    }
    invoice_payload = {
        "balance": balance,
        "current_state": invoice_data.current_state,
        "id": invoice_data.id,
        "line_items": invoice_data.line_items,
        "payment_method": payment_method,
    }

    return render(request, "customer/view_invoice.html", {"invoice": invoice_payload})


@require_http_methods(["GET"])
def customer_view_pdf(request, pk):
    """GET: invoice PDF download/view."""
    try:
        invoice_data = _invoice_for_member(request, pk)
    except PermissionDenied:
        return HttpResponseForbidden()
    except Invoice.DoesNotExist:
        return HttpResponseForbidden()

    payment_intent = stripe.PaymentIntent.retrieve(invoice_data.payment_intent_id)
    payment_method = payment_intent["payment_method"]
    if not payment_method and payment_intent["last_payment_error"]:
        if payment_intent["last_payment_error"]["payment_method"]:
            payment_method = payment_intent["last_payment_error"]["payment_method"]["id"]
    if payment_method:
        payment_method = stripe.PaymentMethod.retrieve(payment_method)
        payment_method = invoice.get_payment_method_json(payment_method, None)
    if invoice_data.tax and invoice_data.tax > 0:
        total = invoice_data.subtotal + invoice_data.tax
        tax_rate = ((invoice_data.tax / invoice_data.subtotal) * 100)
    else:
        total = invoice_data.subtotal
        tax_rate = None

    if invoice_data.processing_fees:
        total += invoice_data.processing_fees

    balance = {
        "subtotal": invoice_data.subtotal,
        "tax": invoice_data.tax,
        "tax_rate": tax_rate,
        "total": total,
        "processing_fees": invoice_data.processing_fees,
    }
    invoice_payload = {
        "balance": balance,
        "current_state": invoice_data.current_state,
        "id": invoice_data.id,
        "line_items": invoice_data.line_items,
        "payment_method": payment_method,
    }

    globalsettings = GlobalSettings.load()
    logo_path = f"file://{globalsettings.login_image.path}"

    hr_timestamp = timezone.localtime(invoice_data.timestamp).strftime("%m/%d/%Y %I:%M:%S %p")

    html_string = render_to_string(
        "customer/pdf_invoice.html",
        {
            "invoice": invoice_payload,
            "logo_path": logo_path,
            "business_name": globalsettings.name,
            "rendering_pdf": True,
            "timestamp": hr_timestamp,
        },
    )

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{pk}.pdf"'
    return response


@require_http_methods(["GET"])
def customer_cancel_invoice(request, pk):
    """GET: cancel an open invoice/PaymentIntent."""
    try:
        inv = _invoice_for_member(request, pk)
    except PermissionDenied:
        return HttpResponseForbidden()
    except Invoice.DoesNotExist:
        return HttpResponseForbidden()

    if inv.current_state in [0, 1, 4]:
        if inv.payment_intent_id:
            stripe.PaymentIntent.cancel(inv.payment_intent_id)

    return redirect(reverse("customer_make_payment"))


@require_http_methods(["GET"])
def customer_parcels(request):
    """GET: customer package list for linked account."""
    account, early = _customer_account_or_response(request)
    if early:
        return early
    account_id = account.id

    packages = Package.objects.select_related(
        "carrier", "packagetype", "packagepicklist"
    ).annotate(
        check_in_time=Max(Case(When(packageledger__state=1, then="packageledger__timestamp"))),
        check_out_time=Max(Case(When(packageledger__state=2, then="packageledger__timestamp"))),
        cost=F("price"),
        picklist_id=F("packagepicklist__picklist_id"),
        picklist_date=F("packagepicklist__picklist__date"),
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
        "check_out_time",
    ).filter(account_id=account_id).order_by("current_state", "-check_in_time")

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(packages, per_page)
    page_obj = paginator.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []

    return render(
        request,
        "customer/parcels.html",
        {"page_obj": page_obj, "selected": selected, "active_account": account},
    )


@require_http_methods(["GET"])
def customer_invoices(request):
    """GET: past invoices for the active account."""
    account, early = _customer_account_or_response(request)
    if early:
        return early

    invoices = (
        Invoice.objects.filter(account=account)
        .order_by("-timestamp")
        .values(
            "id",
            "timestamp",
            "current_state",
            "subtotal",
            "tax",
            "processing_fees",
            "stripe_fee",
            "deposit_total",
        )
    )
    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)
    paginator = Paginator(invoices, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customer/invoices.html",
        {"page_obj": page_obj, "active_account": account},
    )


@require_http_methods(["GET"])
def customer_ledger(request):
    """GET: ledger history for the active account."""
    account, early = _customer_account_or_response(request)
    if early:
        return early

    ledger = (
        AccountLedger.objects.filter(account=account)
        .select_related("user", "package", "invoice")
        .values(
            "credit",
            "debit",
            "timestamp",
            "description",
            "package_id",
            "is_late",
            "user__first_name",
            "user__last_name",
            "package__tracking_code",
            "invoice__id",
        )
        .order_by("-timestamp")
    )
    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)
    paginator = Paginator(ledger, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customer/ledger.html",
        {"page_obj": page_obj, "active_account": account, "account": account},
    )


@require_http_methods(["POST"])
@exception_catcher()
def customer_confirm_invoice(request, pk):
    """POST: confirm and finalize payment for invoice."""
    try:
        invoice_data = _invoice_for_member(request, pk)
    except PermissionDenied:
        return JsonResponse({"success": False, "errors": ["Forbidden"]}, status=403)

    invoice_url = request.build_absolute_uri(
        reverse("customer_view_invoice", kwargs={"pk": invoice_data.id})
    )

    if invoice_data.current_state == 4:
        payment_intent = stripe.PaymentIntent.retrieve(invoice_data.payment_intent_id)
        if payment_intent["last_payment_error"] and payment_intent["last_payment_error"]["payment_method"]:
            payment_method = payment_intent["last_payment_error"]["payment_method"]["id"]
            payment_intent = stripe.PaymentIntent.modify(
                invoice_data.payment_intent_id, payment_method=payment_method
            )

    try:
        payment_intent = stripe.PaymentIntent.confirm(
            invoice_data.payment_intent_id, return_url=invoice_url
        )
    except stripe.InvalidRequestError as e:
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
    """POST: create invoice/PaymentIntent for amount and method."""
    account, early = _customer_account_or_response(request, for_json=True)
    if early:
        return early
    account_id = account.id
    customer_id = invoice.get_customer_id(account_id)

    globalsettings = GlobalSettings.load()

    data = json.loads(request.body)
    method = data["method"]

    subtotal = float(data["amount"])
    if subtotal < 0.50:
        raise ValueError
    line_items = invoice.generate_line_items(subtotal, account_id)

    tax_rate = float(globalsettings.tax_rate / 100) if globalsettings.taxes else 0.00
    tax = round(subtotal * tax_rate, 2) if globalsettings.taxes else None
    total = round((subtotal + tax) * 100) if tax else round(subtotal * 100)

    processing_fees = None
    if globalsettings.pass_on_fees:
        fee_subtotal = tax + subtotal if tax else subtotal
        processing_fees = ((fee_subtotal * 0.029) + 0.30)
        cur_proc_fees = processing_fees * 0.029
        while round(cur_proc_fees, 2) >= 0.01:
            processing_fees += cur_proc_fees
            cur_proc_fees = cur_proc_fees * 0.029

        total += round(processing_fees * 100)

    payment_intent_id, url = None, None
    if method not in ["ONETIME", "NEW"]:
        payment_method = StripePaymentMethod.objects.filter(
            pk=method, customer__customer_id=customer_id
        ).first()
        if not payment_method:
            raise ValueError

        payment_intent = stripe.PaymentIntent.create(
            amount=total,
            payment_method=payment_method.payment_method_id,
            customer=customer_id,
            currency="usd",
        )
        payment_intent_id = payment_intent.id

    invoice_data = Invoice.objects.create(
        account_id=account_id,
        user_id=request.user.id,
        payment_intent_id=payment_intent_id,
        line_items=line_items,
        subtotal=subtotal,
        tax=tax,
        processing_fees=processing_fees,
    )
    invoice_url = request.build_absolute_uri(
        reverse("customer_view_invoice", kwargs={"pk": invoice_data.id})
    )
    success_url = invoice_url + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = f"{invoice_url}/cancel"

    if method == "ONETIME":
        tax_rate_id = globalsettings.tax_stripe_id if globalsettings.taxes else None
        line_items, discount = invoice.generate_checkout_line_items(line_items, tax_rate_id)

        if discount:
            coupon = stripe.Coupon.create(amount_off=discount, currency="usd", name="Account Credit")
            discount = [{"coupon": coupon["id"]}]

        checkout_session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=line_items,
            discounts=discount if discount else [],
            mode="payment",
            ui_mode="hosted",
        )

        url = checkout_session["url"]
    elif method == "NEW":
        checkout_session = stripe.checkout.Session.create(
            mode="setup",
            currency="usd",
            customer=customer_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        url = checkout_session["url"]

    if not url:
        url = invoice_url

    return JsonResponse({"success": True, "url": url})
