import json
import re
from boxes.models import *
from .common import _get_packages, _search_packages_helper
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse

def picklists(request):
    return render(request, "packages/search_picklists.html", {"picklists": True,
                                                              "picklist_data": _picklist_data(),
                                                              "search_url": reverse("search_picklist_packages")})

def search_picklist_packages(request):
    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("picklists")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []
    query = request.GET.get("q", "")
    filter_info = request.GET.get("filter", "")

    return render(request, "packages/search_picklists.html", {"picklists": True,
                                                              "picklist_data": _picklist_data(),
                                                              "page_obj": page_obj,
                                                              "selected": selected,
                                                              "query": query,
                                                              "filter": filter_info})

@require_POST
def add_package_picklist(request):
    try:
        data = json.loads(request.body)
        picklist_id = int(data.get("picklist_id"))
        package_ids = data.get("ids", [])

        package_picklist_objects = [
            PackagePicklist(package_id=pkgid, picklist_id=picklist_id) for pkgid in package_ids
        ]
        with transaction.atomic():
            PackagePicklist.objects.bulk_create(package_picklist_objects)
        
        messages.success(request, "Successfully added to picklist")
        return JsonResponse({"success": True, "redirect_url": reverse("picklists")})
    except ValueError as e:
        messages.error(request, "Invalid input")
        return JsonResponse({"success": False, "errors": ["Invalid input provided."]})
    except Exception as e:
        messages.error(request, "An unknown error occurred.")
        return JsonResponse({"success": False, "errors": [str(e)]})

def picklist_show(request, pk):
    picklist = get_object_or_404(Picklist, pk=pk)
    package_ids = PackagePicklist.objects.filter(picklist_id=picklist.id).values_list("package_id", flat=True)

    packages = _get_packages(id__in=package_ids)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    picklist_title = picklist.date if picklist.date else picklist.description

    return render(request, "packages/picklist.html", {"search_url": reverse("search_packages"),
                                                      "page_obj": page_obj,
                                                      "picklist_title": picklist_title})


def _picklist_data():
    picklists = Picklist.objects.all()
    picklist_data = [{"id": picklist.id, "text": f"{picklist.date}"} for picklist in picklists]
    return picklist_data
