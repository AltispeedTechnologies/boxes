import stripe
from decimal import Decimal
from django.conf import settings
from boxes.models import (Account, AccountLedger, AccountStripeCustomer, Package, PackageLedger, StripePaymentMethod,
                          UserAccount)
from django.db.models import Case, Count, DecimalField, F, IntegerField, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce


# Set the stripe API key from our local configuration
stripe.api_key = settings.STRIPE_API_KEY


def get_customer_id(user_id):
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


def get_payment_method_json(pm, pm_id):
    match pm["type"]:
        case "card":
            last4 = f"ending in {pm['card']['last4']} (Expires: {pm['card']['exp_month']}/{pm['card']['exp_year']})"
            return {
                "id": pm_id,
                "brand": pm["card"]["brand"],
                "last4": last4
            }
        case "cashapp":
            return {
                "id": pm_id,
                "brand": "cashapp",
                "last4": f"Cash App Pay: {pm['cashapp']['cashtag']}"
            }
        case "amazon_pay":
            return {
                "id": pm_id,
                "brand": "amazon_pay",
                "last4": "Amazon Pay"
            }
        case "acss_debit" | "us_bank_account":
            bank_info = pm[pm["type"]]
            return {
                "id": pm_id,
                "brand": "bank",
                "last4": f"{bank_info['bank_name']} account ending in {bank_info['last4']}"
            }


def get_payment_methods(user_id):
    # Stripe-formatted customer ID
    customer_id = get_customer_id(user_id)
    # DB customer ID
    customer_pk = AccountStripeCustomer.objects.get(customer_id=customer_id).pk

    # Get the full payment methods from Stripe
    stripe_payment_methods = stripe.Customer.list_payment_methods(customer_id).data
    # Get the Stripe IDs for the payment methods
    stripe_pm_ids = [pm["id"] for pm in stripe_payment_methods]
    # Get the DB IDs for the customer
    db_pm_ids = StripePaymentMethod.objects.filter(
        customer_id=customer_pk
    ).values_list("id", "payment_method_id")
    db_pm_dict = {p[1]: p[0] for p in db_pm_ids}

    # Ensure the DB exactly matches Stripe
    pm_add = [pm for pm in stripe_pm_ids if pm not in db_pm_dict.keys()]
    pm_del = [pm for pm in db_pm_dict.keys() if pm not in stripe_pm_ids]
    for pm in pm_add:
        StripePaymentMethod.objects.create(customer_id=customer_pk, payment_method_id=pm)
    if len(pm_del) > 0:
        StripePaymentMethod.objects.filter(payment_method_id__in=pm_del).delete()

    # If the data was updated, run the query again for fresh data
    if len(pm_add) > 0 or len(pm_del) > 0:
        db_pm_ids = StripePaymentMethod.objects.filter(
            customer_id=customer_pk
        ).values_list("id", "payment_method_id")
        db_pm_dict = {p[1]: p[0] for p in db_pm_ids}

    # Convert into a lighter object for rendering
    payment_methods = [get_payment_method_json(pm, db_pm_dict.get(pm["id"])) for pm in stripe_payment_methods]

    default_method, default_method_id = None, None
    default_method_id = stripe.Customer.retrieve(customer_id)["invoice_settings"]["default_payment_method"]
    if default_method_id:
        for pm in payment_methods:
            if db_pm_dict.get(default_method_id) == pm["id"]:
                default_method = pm
                break
    elif len(payment_methods) > 0:
        default_method = payment_methods[0]

    return payment_methods, default_method


def get_billing_portal_id():
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


def generate_line_items(amount, user_id):
    if amount <= 0:
        return None

    account_id = UserAccount.objects.get(user_id=user_id).account_id

    # Subquery to get the latest PackageLedger timestamp for each package with state 1
    latest_ledger_timestamp = PackageLedger.objects.filter(
        package=OuterRef("pk"),
        state=1
    ).values("timestamp").order_by("-timestamp")[:1]

    # Subquery to calculate the net sum of debits and credits for late entries
    net_sum_late = AccountLedger.objects.filter(
        package=OuterRef("pk"),
        is_late=True
    ).values("package").annotate(
        net_sum=Sum(
            Case(When(debit__isnull=False, then=F("debit")), default=Value(0), output_field=DecimalField())
        ) - Sum(
            Case(When(credit__isnull=False, then=F("credit")), default=Value(0), output_field=DecimalField())
        )
    ).values("net_sum")[:1]

    # Subquery to calculate the net sum of debits and credits for regular entries
    net_sum_regular = AccountLedger.objects.filter(
        package=OuterRef("pk"),
        is_late=False
    ).values("package").annotate(
        net_sum=Sum(
            Case(When(debit__isnull=False, then=F("debit")), default=Value(0), output_field=DecimalField())
        ) - Sum(
            Case(When(credit__isnull=False, then=F("credit")), default=Value(0), output_field=DecimalField())
        )
    ).values("net_sum")[:1]

    # Filter and annotate packages
    packages = Package.objects.filter(
        account_id=account_id,
        current_state=1,
        paid=False
    ).annotate(
        latest_ledger_timestamp=Subquery(latest_ledger_timestamp),
        sum_late=Coalesce(
            Subquery(net_sum_late, output_field=DecimalField()),
            Value(0.00, output_field=DecimalField())
        ),
        sum_normal=Coalesce(
            Subquery(net_sum_regular, output_field=DecimalField()),
            Value(0.00, output_field=DecimalField())
        ),
        count_late=Count(Case(When(accountledger__is_late=True, then=Value(1)), output_field=IntegerField())),
    ).order_by("latest_ledger_timestamp")

    credit_amount = None
    total_charges = sum(p.sum_normal for p in packages) + sum(p.sum_late for p in packages)
    current_balance = Account.objects.get(pk=account_id).balance * -1
    if total_charges > current_balance:
        credit_amount = total_charges - current_balance
        amount += float(credit_amount)

    _iter_amount = amount
    line_items = []
    for package in packages:
        if _iter_amount <= 0:
            continue

        process_late_fees = True if package.sum_late > 0 else False
        partial = False
        if package.sum_normal > _iter_amount:
            package.sum_normal = _iter_amount
            process_late_fees, partial = False, True

        _iter_amount -= float(package.sum_normal)
        line_items.append({
            "id": package.id,
            "amt": float(package.sum_normal),
            "qty": 1,
            "prtl": partial,
            "late": False,
            "trk": package.tracking_code,
        })

        if process_late_fees:
            per_fee = float(package.sum_late / package.count_late)
            if per_fee > _iter_amount:
                continue
            elif package.sum_late > _iter_amount:
                package.sum_late = float(package.sum_late)
                while package.sum_late > _iter_amount:
                    package.sum_late -= per_fee
                    package.count_late -= 1
                package.count_late -= 1
                line_items.append({
                    "id": package.id,
                    "amt": per_fee,
                    "qty": package.count_late,
                    "prtl": False,
                    "late": True,
                    "trk": package.tracking_code,
                })
                line_items.append({
                    "id": package.id,
                    "amt": package.sum_late - (per_fee * package.count_late),
                    "qty": 1,
                    "prtl": True,
                    "late": True,
                    "trk": package.tracking_code,
                })
            else:
                line_items.append({
                    "id": package.id,
                    "amt": per_fee,
                    "qty": package.count_late,
                    "prtl": False,
                    "late": True,
                    "trk": package.tracking_code,
                })

            _iter_amount -= package.sum_late

    if _iter_amount > 0:
        line_items.append({
            "id": None,
            "amt": _iter_amount,
            "qty": 1,
            "prtl": False,
            "late": False,
            "trk": None,
        })

    if credit_amount:
        line_items.append({
            "id": None,
            "amt": float(credit_amount * -1),
            "qty": 1,
            "prtl": False,
            "late": False,
            "trk": None,
        })

    return line_items


def generate_checkout_line_items(line_items, tax_rate_id="txr_1PaKlH2NxJYbIf8PrzWrQ57E"):
    # We already generated these line items
    new_line_items = [
        {
            "price_data": {
                "currency": "usd",
                "tax_behavior": "exclusive",
                "unit_amount_decimal": line_item["amt"] * 100,
                "product_data": {
                    "name": (
                        f"PARTIAL " if line_item["trk"] and line_item["prtl"] else ""
                    ) + (
                        f"Late fee for {line_item['trk']}" if line_item["trk"] and line_item["late"] else
                        (f"Parcel fee for {line_item['trk']}" if line_item["trk"] else "Credit Balance")
                    )
                }
            },
            "quantity": line_item["qty"],
            "tax_rates": [tax_rate_id]
        }
        for line_item in line_items if line_item["amt"] > 0
    ]

    # Account for discounts, which are converted into coupons
    discount = round(sum(abs(i["amt"]) for i in line_items if i["amt"] < 0) * 100)
    discount = None if discount == 0 else discount

    return new_line_items, discount
