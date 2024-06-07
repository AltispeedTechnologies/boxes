import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Package, PackagePicklist, PackageQueue, Picklist, PicklistQueue, Queue
from boxes.views.packages.utility import update_packages_util
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def check_out(request):
    # Check if there is already a PicklistQueue mapping
    queue, _ = Queue.objects.get_or_create(description="Check Out Queue", check_in=False)

    # Grab all packages in the queue
    package_ids = list(PackageQueue.objects.filter(queue_id=queue.id).values_list("package_id", flat=True))

    packages = Package.objects.select_related("account").values(
        "id",
        "account_id",
        "price",
        "tracking_code",
        "comments"
    ).annotate(
        account=F("account__name")
    ).filter(id__in=package_ids)

    return render(request, "packages/check_out.html", {"packages": packages,
                                                       "package_ids": package_ids})


@require_http_methods(["POST"])
@exception_catcher()
def check_out_packages(request):
    result = update_packages_util(request, state=2, debit_credit_switch=True)
    if not result["success"]:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occured."])})


@require_http_methods(["POST"])
@exception_catcher()
def check_out_packages_reverse(request):
    result = update_packages_util(request, state=1, debit_credit_switch=False)
    if not result["success"]:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occured."])})


@require_http_methods(["POST"])
@exception_catcher()
def verify_can_checkout(request):
    data = json.loads(request.body)
    tracking_code = str(data.get("tracking_code"))
    picklist_id = data.get("picklist_id", None)

    # Get the Package matching the tracking code with a current state of 1
    package = Package.objects.select_related("account").values(
        "id",
        "account_id",
        "price",
        "tracking_code",
        "comments",
        "current_state"
    ).annotate(
        account=F("account__name")
    ).filter(tracking_code=tracking_code).first()

    if package is None:
        return JsonResponse({"success": False, "errors": ["Parcel not found"]})

    if package["current_state"] == 2:
        return JsonResponse({"success": False, "errors": ["Parcel already checked out"]})
    elif package["current_state"] == 0:
        return JsonResponse({"success": False, "errors": ["Parcel not checked in yet"]})

    if picklist_id:
        picklist = get_object_or_404(Picklist, pk=picklist_id)
        in_picklist = PackagePicklist.objects.filter(picklist_id=picklist.id, package_id=package["id"]).exists()

        if in_picklist:
            with transaction.atomic():
                # Ensure a Queue exists and add to it
                picklist_queue = PicklistQueue.objects.filter(picklist_id=picklist.id).first()
                if not picklist_queue:
                    queue = Queue.objects.create(description="", check_in=False)
                    picklist_queue = PicklistQueue.objects.create(picklist_id=picklist.id, queue_id=queue.id)
                else:
                    queue = Queue.objects.filter(pk=picklist_queue.queue_id).first()

                # If the package is already in the Queue, error appropriately
                if PackageQueue.objects.filter(package_id=package["id"], queue_id=queue.id).exists():
                    return JsonResponse({"success": False, "errors": ["Parcel already in queue"]})

                # Create the queue entry
                PackageQueue.objects.create(package_id=package["id"], queue_id=queue.id)

                # Remove from the picklist
                PackagePicklist.objects.filter(picklist_id=picklist.id, package_id=package["id"]).delete()

                return JsonResponse({"success": True, "package": package})
        else:
            return JsonResponse({"success": False, "errors": ["Specified parcel not in picklist"]})
    else:
        with transaction.atomic():
            queue, _ = Queue.objects.get_or_create(description="Check Out Queue", check_in=False)

            # If the package is already in the Queue, error appropriately
            if PackageQueue.objects.filter(package_id=package["id"], queue_id=queue.id).exists():
                return JsonResponse({"success": False, "errors": ["Parcel already in queue"]})

            # Create the queue entry
            PackageQueue.objects.create(package_id=package["id"], queue_id=queue.id)

            return JsonResponse({"success": True, "package": package})
