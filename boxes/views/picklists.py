import re
from boxes.models import *
from .common import _get_packages, _search_packages_helper
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
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

def _picklist_data():
    picklists = Picklist.objects.all()
    picklist_data = [{"id": picklist.id, "text": f"{picklist.date}"} for picklist in picklists]
    return picklist_data
