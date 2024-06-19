import json
import re
from boxes.management.exception_catcher import exception_catcher
from boxes.models import *
from .common import _get_packages, _search_packages_helper
from datetime import datetime
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
    return JsonResponse({"success": True, "results": results})


@require_http_methods(["POST"])
@exception_catcher()
def create_picklist(request):
    data = json.loads(request.body)
    description = data.get("description", None)
    date = data.get("date", None)

    if not description and not date:
        raise ValueError

    if date:
        # MM/DD/YYYY
        pattern = r"^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/(20[0-9][0-9])$"
        if not re.match(pattern, date):
            raise ValueError

        date = datetime.strptime(date, "%m/%d/%Y").date()

    # Do not allow duplicates to be created
    if Picklist.objects.filter(date=date, description=description):
        raise RuntimeError("Picklist already exists")

    picklist = Picklist.objects.create(date=date, description=description)

    # Human-readable value is MONTH DAY, YEAR
    if date:
        date = date.strftime("%B %d, %Y")

    return JsonResponse({"success": True, "new_id": picklist.id, "hr_date": date})


@require_http_methods(["POST"])
@exception_catcher()
def modify_package_picklist(request):
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


@require_http_methods(["POST"])
@exception_catcher()
def remove_package_picklist(request):
    data = json.loads(request.body)
    package_ids = set(data.get("ids", []))

    if not package_ids:
        messages.error(request, "No package IDs provided.")
        return JsonResponse({"success": False, "errors": ["No package IDs provided."]})

    package_ids = [int(pkg_id) for pkg_id in package_ids]
    PackagePicklist.objects.filter(package_id__in=package_ids).delete()

    messages.success(request, "Successfully removed packages from picklist")
    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@exception_catcher()
def remove_picklist(request, pk):
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
            if queue:
                queue_id = queue.queue_id
                PackageQueue.objects.filter(queue_id=queue_id).delete()
                queue.delete()

        # Delete the picklist
        Picklist.objects.filter(pk=pk).delete()

    return JsonResponse({"success": True, "new_count": new_count, "new_queue_count": new_queue_count})


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
        ),
        is_date_null=Case(
            When(date__isnull=True, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by("is_date_null", "date", "description")

    return render(request, "picklists/picklist_list.html", {"picklists": picklists})


@require_http_methods(["GET"])
def picklist_show(request, pk=None):
    picklist = get_object_or_404(Picklist, pk=pk)

    package_ids = PackagePicklist.objects.filter(picklist_id=picklist.id).values_list("package_id", flat=True)

    packages = _get_packages(id__in=package_ids)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    picklist_title = picklist.date if picklist.date else picklist.description

    return render(request, "picklists/packages.html", {"page_obj": page_obj,
                                                       "picklists": True,
                                                       "view_type": "packages",
                                                       "picklist_data": _picklist_data(exclude=picklist.id),
                                                       "picklist_title": picklist_title,
                                                       "picklist_id": picklist.id})


@require_http_methods(["GET"])
def picklist_show_table(request, pk=None):
    picklist = get_object_or_404(Picklist, pk=pk)
    picklist_title = picklist.date if picklist.date else picklist.description

    package_ids = PackagePicklist.objects.filter(picklist_id=picklist.id).values_list("package_id", flat=True)

    packages = _get_packages(id__in=package_ids)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "packages/_table.html", {"page_obj": page_obj,
                                                    "picklist_data": _picklist_data(exclude=picklist.id),
                                                    "picklist_title": picklist_title})


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

    picklists = picklists.annotate(
        is_date_null=Case(
            When(date__isnull=True, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by("is_date_null", "date", "description")

    picklist_data = []
    for picklist in picklists:
        if picklist.date and picklist.description:
            text = str(picklist.date) + " - " + picklist.description
        elif picklist.date:
            text = str(picklist.date)
        elif picklist.description:
            text = picklist.description

        picklist_data.append({"id": picklist.id, "text": text})

    return picklist_data
