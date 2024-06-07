import decimal
import json
from boxes.models import AccountChargeSettings, PackageType
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


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

    package_types = PackageType.objects.all().values("id", "description")
    return render(request, "mgmt/charges.html", {"charge_rules": charge_rules,
                                                 "custom_charge_rules": custom_charge_rules,
                                                 "endpoint": endpoint,
                                                 "package_types": package_types})


@require_http_methods(["POST"])
def save_charge_settings(request):
    data = json.loads(request.body)

    AccountChargeSettings.objects.all().delete()
    for rule in data:
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

    return JsonResponse({"success": True})
