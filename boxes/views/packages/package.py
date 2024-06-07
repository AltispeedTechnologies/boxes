import json
from boxes.models import Package, PackageLedger, SentEmail
from boxes.models.package import PACKAGE_STATES
from boxes.views.packages.utility import update_packages_fields
from django.db.models import F
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def package_detail(request, pk):
    package_values = Package.objects.select_related("account", "carrier", "packagetype").values(
        "id",
        "price",
        "carrier__name",
        "account__name",
        "package_type__description",
        "tracking_code",
        "comments",
    ).filter(id=pk).first()

    state_ledger = PackageLedger.objects.select_related("user").values(
        "user__first_name",
        "user__last_name",
        "state",
        "timestamp",
    ).filter(package_id=pk)

    page_obj = SentEmail.objects.filter(
        sentemailpackage__package__id=pk
    ).annotate(
        sent_id=F("pk"),
        timestamp_val=F("timestamp"),
        subject_val=F("subject"),
        email_val=F("email"),
        status=F("success")
    ).order_by("-timestamp_val")

    state_names = dict(PACKAGE_STATES)
    for entry in state_ledger:
        entry["state"] = state_names.get(entry["state"], "Unknown")

    return render(request, "packages/package.html", {"package": package_values,
                                                     "state_ledger": state_ledger,
                                                     "enable_tracking_codes": False,
                                                     "page_obj": page_obj})


@require_http_methods(["POST"])
def update_package(request, pk):
    request_data = json.loads(request.body)
    result = update_packages_fields([pk], request_data, request.user)
    return result


@require_http_methods(["POST"])
def update_packages(request):
    request_data = json.loads(request.body)
    package_ids = request_data.get("ids")
    package_data = request_data.get("values")
    no_ledger = request_data.get("no_ledger")

    result = update_packages_fields(package_ids, package_data, request.user, no_ledger)
    return result
