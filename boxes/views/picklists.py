import json
import re
from boxes.models import *
from .common import _get_packages, _search_packages_helper
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.urls import reverse

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
        return JsonResponse({"success": False, "errors": ["Invalid input provided. Ensure all package IDs are integers."]})
    except Exception as e:
        messages.error(request, "An unknown error occurred.")
        return JsonResponse({"success": False, "errors": [str(e)]})

@require_http_methods(["GET"])
def picklist_show(request, pk=None):
    if pk:
        picklist = get_object_or_404(Picklist, pk=pk)
    else:
        picklist = Picklist.objects.first()

    package_ids = PackagePicklist.objects.filter(picklist_id=picklist.id).values_list("package_id", flat=True)

    packages = _get_packages(id__in=package_ids)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    picklist_title = picklist.date if picklist.date else picklist.description

    return render(request, "packages/picklist.html", {"search_url": reverse("search_packages"),
                                                      "page_obj": page_obj,
                                                      "picklists": True,
                                                      "picklist_data": _picklist_data(exclude=picklist.id),
                                                      "picklist_title": picklist_title})


def _picklist_data(exclude=None):
    if exclude:
        picklists = Picklist.objects.exclude(id=exclude)
    else:
        picklists = Picklist.objects.all()

    picklist_data = [{"id": picklist.id, "text": f"{picklist.date}"} for picklist in picklists]

    return picklist_data
