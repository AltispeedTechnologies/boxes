import json
"""Package check-in UI and creation."""
from boxes.forms import PackageForm
from boxes.management.exception_catcher import exception_catcher
from boxes.models import (Account, Carrier, EmailQueue, EmailSettings, Package, PackageQueue,
                          PackageSystemTrackingCode, PackageType, Queue)
from boxes.views.packages.utility import tracking_code_conflict, update_packages_util
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def check_in(request):
    """GET: check-in page with queue selector."""
    form = PackageForm()
    queues = Queue.objects.filter(check_in=True)
    prices = PackageType.objects.filter(is_active=True).values_list("default_price", flat=True)
    return render(request, "packages/create.html", {"form": form,
                                                    "queues": queues,
                                                    "prices": prices})


@require_http_methods(["POST"])
@exception_catcher()
def create_package(request):
    # If the tracking code is None, this means we need to generate one
    # (An empty tracking code should give the user an error)
    """POST: create a package (and queue membership) from form or JSON body."""
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"success": False, "errors": ["Invalid JSON"]})
        data = {k: ("" if v is None else str(v)) for k, v in payload.items()}
        # Checkbox-style fields
        if "inside" in payload:
            data["inside"] = "on" if payload.get("inside") in (True, "true", "1", "on", 1) else ""
    else:
        data = request.POST.copy()
    return_tracking_code = False
    generate_raw = data.get("generate_tracking", "")
    generate_tracking = str(generate_raw).lower() in ("1", "true", "yes", "on")
    data.pop("generate_tracking", None)

    if not (data.get("tracking_code") or "").strip():
        if generate_tracking:
            tracking_code, created = PackageSystemTrackingCode.objects.get_or_create(
                prefix="INT"
            )
            tracking_code.last_number = F("last_number") + 1
            tracking_code.save()
            tracking_code.refresh_from_db()
            data["tracking_code"] = (
                f"{tracking_code.prefix}{tracking_code.last_number:010d}"
            )
            return_tracking_code = True
        # else leave empty; PackageForm requires tracking_code

    form = PackageForm(data)
    if form.is_valid():
        package = form.save(commit=False)

        queue_id = form.cleaned_data["queue_id"]

        # Use helper functions
        package.carrier = Carrier.objects.get(id=form.cleaned_data["carrier_id"])
        package.account = Account.objects.get(id=form.cleaned_data["account_id"])
        package.package_type = PackageType.objects.get(id=form.cleaned_data["package_type_id"])

        conflict = tracking_code_conflict(
            package.carrier, package.tracking_code
        )
        if conflict:
            return JsonResponse({
                "success": False,
                "form_errors": {"tracking_code": [conflict]},
            })

        package.save()
        PackageQueue.objects.create(package=package, queue_id=queue_id)
        if return_tracking_code:
            return JsonResponse({"success": True, "id": package.id, "tracking_code": package.tracking_code})
        else:
            return JsonResponse({"success": True, "id": package.id})
    else:
        return JsonResponse({"success": False, "form_errors": form.errors})


@require_http_methods(["POST"])
@exception_catcher()
def check_in_packages(request):
    """POST: transition selected packages to checked-in state."""
    queue_id = request.POST.get("queue_id")
    PackageQueue.objects.filter(queue_id=queue_id).delete()

    result = update_packages_util(request, state=1, debit_credit_switch=False)
    ids = request.POST.getlist("ids[]", [])
    check_in_template = EmailSettings.objects.values_list("check_in_template", flat=True).first()
    if check_in_template is not None:
        for package_id in ids:
            EmailQueue.objects.create(package_id=package_id, template_id=check_in_template)

    if not result["success"]:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occured."])})
    return JsonResponse({"success": True})
