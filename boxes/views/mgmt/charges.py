import decimal
import json
import stripe
from boxes.models import AccountChargeSettings, GlobalSettings, PackageType
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


# Set the stripe API key from our local configuration
stripe.api_key = settings.STRIPE_API_KEY


@require_http_methods(["GET"])
def charge_settings(request):
    charge_rules = AccountChargeSettings.objects.filter(
        package_type_id__isnull=True,
        price__isnull=True,
        frequency__isnull=True,
        endpoint__isnull=True
    ).order_by("days")

    custom_charge_rules = AccountChargeSettings.objects.filter(
        package_type_id__isnull=False,
        price__isnull=False,
        frequency__isnull=False,
        endpoint__isnull=True
    ).order_by("days")

    endpoint = AccountChargeSettings.objects.filter(
        endpoint__isnull=False
    ).values_list("endpoint", flat=True).first()

    globalsettings, _ = GlobalSettings.objects.get_or_create(id=1)

    package_types = PackageType.objects.all().values("id", "description")
    return render(request, "mgmt/charges.html", {"charge_rules": charge_rules,
                                                 "custom_charge_rules": custom_charge_rules,
                                                 "endpoint": endpoint,
                                                 "package_types": package_types,
                                                 "globalsettings": globalsettings})


def get_tax_rate(tax_rate):
    # If there is an existing tax with the new percentage, simply re-enable it
    # Otherwise, create a new TaxRate
    tax_rates = stripe.TaxRate.list()
    target, last = None, None
    while (tax_rates["has_more"] or len(tax_rates["data"]) > 0) and not target:
        for tr in tax_rates:
            last = tr["id"]
            if not target:
                target = tr["id"] if tr["percentage"] == tax_rate else None
        tax_rates = stripe.TaxRate.list(starting_after=last)

    if target:
        stripe.TaxRate.modify(target, active=True)
        tax_rate_id = target
    else:
        tr = stripe.TaxRate.create(display_name="Sales Tax", percentage=tax_rate, inclusive=False)
        tax_rate_id = tr["id"]

    return tax_rate_id


@require_http_methods(["POST"])
def save_charge_settings(request):
    data = json.loads(request.body)

    AccountChargeSettings.objects.all().delete()
    for rule in data["charge_rules"]:
        package_type_id = rule.get("package_type_id")
        days = rule.get("days")
        price = rule.get("price")
        frequency = rule.get("frequency")
        endpoint = rule.get("endpoint")

        AccountChargeSettings.objects.create(
            package_type_id=package_type_id,
            days=int(days) if days else None,
            price=decimal.Decimal(price) if price else None,
            frequency=frequency,
            endpoint=int(endpoint) if endpoint else None
        )

    # Grab the only global settings present
    globalsettings, _ = GlobalSettings.objects.get_or_create(id=1)

    # Validate the tax rate, if present
    tax_rate = None
    if "tax_rate" in data["misc_charges"]:
        tax_rate = float(data["misc_charges"]["tax_rate"])
        if tax_rate <= 0 or tax_rate >= 100:
            raise ValueError

    # If toggling taxes, set the values appropriately
    taxes = data["misc_charges"]["taxes"]
    # Disabling taxes
    if globalsettings.taxes and not taxes:
        stripe.TaxRate.modify(globalsettings.tax_stripe_id, active=False)
        globalsettings.tax_stripe_id = None
        globalsettings.tax_rate = None
    # Enabling taxes
    elif not globalsettings.taxes and taxes:
        globalsettings.tax_stripe_id = get_tax_rate(tax_rate)
        globalsettings.tax_rate = tax_rate
    # Updating the tax rate
    elif tax_rate and taxes and tax_rate != globalsettings.tax_rate:
        stripe.TaxRate.modify(globalsettings.tax_stripe_id, active=False)
        globalsettings.tax_stripe_id = get_tax_rate(tax_rate)
        globalsettings.tax_rate = tax_rate

    globalsettings.taxes = taxes

    # Independent bool, set to current value
    globalsettings.pass_on_fees = data["misc_charges"]["pass_on_fees"]
    globalsettings.save()

    return JsonResponse({"success": True})
