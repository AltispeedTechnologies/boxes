import json
import re
from boxes.models import *
from .common import _get_packages, _search_packages_helper
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import *
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.timezone import localtime


@require_http_methods(["GET"])
def picklist_query(request):
    results = _picklist_data()
    return JsonResponse({"results": results})


@require_http_methods(["POST"])
def modify_package_picklist(request):
    try:
        data = json.loads(request.body)
        picklist_id = int(data.get("picklist_id"))
        package_ids = set(data.get("ids", []))

        existing_entries = PackagePicklist.objects.filter(package_id__in=package_ids)
        existing_entries.update(picklist_id=picklist_id)
        existing_package_ids = set(existing_entries.values_list("package_id", flat=True))

        # Ensure consistent data types for the set subtraction
        package_ids = {int(pkg_id) for pkg_id in package_ids}
        existing_package_ids = {int(pkg_id) for pkg_id in existing_package_ids}

        new_package_ids = package_ids - existing_package_ids
        new_objects = [PackagePicklist(package_id=pkg_id, picklist_id=picklist_id) for pkg_id in new_package_ids]

        if new_objects:
            with transaction.atomic():
                PackagePicklist.objects.bulk_create(new_objects)

        return JsonResponse({"success": True})
    except ValueError:
        messages.error(request, "Invalid input")
        return JsonResponse({"success": False, "errors": ["Invalid input provided."]})
    except Exception as e:
        messages.error(request, "An unknown error occurred.")
        return JsonResponse({"success": False, "errors": [str(e)]})


@require_http_methods(["POST"])
def picklist_verify_can_checkout(request, pk):
    try:
        picklist = get_object_or_404(Picklist, pk=pk)

        data = json.loads(request.body)
        tracking_code = str(data.get("tracking_code"))

        # Get the Package matching the tracking code with a current state of 1
        package = Package.objects.select_related("account").values(
            "id",
            "account_id",
            "price",
            "tracking_code",
            "comments"
        ).annotate(
            account=F("account__name")
        ).filter(tracking_code=tracking_code, current_state=1).first()

        if package is None:
            return JsonResponse({"success": False, "errors": ["Parcel not found"]})

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
    except ValueError:
        return JsonResponse({"success": False, "errors": ["Invalid input provided."]})
    except Exception as e:
        return JsonResponse({"success": False, "errors": [str(e)]})


@require_http_methods(["POST"])
def remove_package_picklist(request):
    try:
        data = json.loads(request.body)
        package_ids = set(data.get("ids", []))

        if not package_ids:
            messages.error(request, "No package IDs provided.")
            return JsonResponse({"success": False, "errors": ["No package IDs provided."]})

        package_ids = [int(pkg_id) for pkg_id in package_ids]
        PackagePicklist.objects.filter(package_id__in=package_ids).delete()

        messages.success(request, "Successfully removed packages from picklist")
        return JsonResponse({"success": True})
    except ValueError:
        messages.error(request, "Invalid input")
        return JsonResponse({"success": False, "errors": ["Invalid input provided."]})
    except Exception as e:
        messages.error(request, "An unknown error occurred.")
        return JsonResponse({"success": False, "errors": [str(e)]})


@require_http_methods(["POST"])
def remove_picklist(request, pk):
    try:
        data = json.loads(request.body)
        picklist_id_value = data.get("picklist_id")
        new_picklist = int(picklist_id_value) if picklist_id_value else None

        with transaction.atomic():
            new_count, new_queue_count = None, None
            if new_picklist:
                PackagePicklist.objects.filter(picklist_id=pk).update(picklist_id=new_picklist)

                # Get the number of items in the picklist
                new_count = PackagePicklist.objects.filter(picklist_id=new_picklist).count()

                # If a checkout queue exists, make sure it's cleaned up
                # Additionally, ensure all packages in the corresponding check in queue are moved
                old_queue = PicklistQueue.objects.filter(picklist_id=pk).first()
                if old_queue:
                    old_queue_id = old_queue.queue_id
                    new_picklist_queue = PicklistQueue.objects.filter(picklist_id=new_picklist).first()

                    if not new_picklist_queue:
                        # If there's no queue for the new picklist, create it
                        queue = Queue.objects.create(description="", check_in=False)
                        new_queue_id = queue.id
                        PicklistQueue.objects.create(queue_id=new_queue_id, picklist_id=new_picklist)
                    else:
                        new_queue_id = new_picklist_queue.queue_id

                    # Update all packages in the old queue to be in the new queue
                    PackageQueue.objects.filter(queue_id=old_queue_id).update(queue_id=new_queue_id)

                    # Ensure we know how many packages are in the new queue
                    new_queue_count = PackageQueue.objects.filter(queue_id=new_queue_id).count()

                    # Delete the old picklist queue and queue itself
                    PicklistQueue.objects.filter(queue_id=old_queue_id, picklist_id=pk).delete()
                    Queue.objects.filter(pk=old_queue_id).delete()
            else:
                PackagePicklist.objects.filter(picklist_id=pk).delete()
                queue = PicklistQueue.objects.filter(picklist_id=pk).first()
                queue_id = queue.queue_id
                PackageQueue.objects.filter(queue_id=queue_id).delete()
                queue.delete()

            # Delete the picklist
            Picklist.objects.filter(pk=pk).delete()

        return JsonResponse({"success": True, "new_count": new_count, "new_queue_count": new_queue_count})
    except ValueError:
        return JsonResponse({"success": False, "errors": ["Invalid input provided."]})
    except Exception as e:
        return JsonResponse({"success": False, "errors": [str(e)]})


@require_http_methods(["GET"])
def picklist_list(request, pk=None):
    picklists = Picklist.objects.annotate(
        count=Count("packagepicklist"),
        queue_count=Coalesce(Subquery(
            PicklistQueue.objects.filter(picklist_id=OuterRef("id"))
            .annotate(
                package_count=Count("queue__packagequeue")
            )
            .values("package_count")[:1]
        ), 0),
        today=Case(
            When(date=localtime().date(), then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        ),
        past=Case(
            When(date__lt=localtime().date(), then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by("date")

    return render(request, "picklists/picklist_list.html", {"picklists": picklists})


@require_http_methods(["GET"])
def picklist_show(request, pk=None):
    picklist = get_object_or_404(Picklist, pk=pk)

    package_ids = PackagePicklist.objects.filter(picklist_id=picklist.id).values_list("package_id", flat=True)

    packages = _get_packages(id__in=package_ids)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    picklist_title = picklist.date if picklist.date else picklist.description

    return render(request, "picklists/packages.html", {"search_url": reverse("search_packages"),
                                                       "page_obj": page_obj,
                                                       "picklists": True,
                                                       "view_type": "packages",
                                                       "picklist_data": _picklist_data(exclude=picklist.id),
                                                       "picklist_title": picklist_title,
                                                       "picklist_id": picklist.id})


@require_http_methods(["GET"])
def picklist_check_out(request, pk=None):
    picklist = get_object_or_404(Picklist, pk=pk)

    picklist_title = picklist.date if picklist.date else picklist.description

    # By default, no packages are rendered
    packages = None
    package_ids = []
    # Check if there is already a PicklistQueue mapping
    picklist_queue = PicklistQueue.objects.filter(picklist_id=picklist.id).first()
    if picklist_queue:
        # Find the queue mapped
        queue_id = picklist_queue.queue_id
        queue = Queue.objects.filter(pk=queue_id)
        if queue:
            # Grab all packages in the queue
            package_ids = list(PackageQueue.objects.filter(queue_id=queue_id).values_list("package_id", flat=True))

            packages = Package.objects.select_related("account").values(
                "id",
                "account_id",
                "price",
                "tracking_code",
                "comments"
            ).annotate(
                account=F("account__name")
            ).filter(id__in=package_ids)

    return render(request, "picklists/checkout.html", {"picklists": True,
                                                       "view_type": "check_out",
                                                       "picklist_title": picklist_title,
                                                       "picklist_id": picklist.id,
                                                       "packages": packages,
                                                       "package_ids": package_ids})


def _picklist_data(exclude=None):
    if exclude:
        picklists = Picklist.objects.exclude(id=exclude)
    else:
        picklists = Picklist.objects.all()

    picklist_data = [{"id": picklist.id, "text": f"{picklist.date}"} for picklist in picklists]

    return picklist_data
