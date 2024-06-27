from boxes.views.common import _search_packages_helper
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def all_packages(request):
    return render(request, "packages/index.html", {"search_url": reverse("search_packages"),
                                                   "filter": "customer"})


@require_http_methods(["GET"])
def search_packages(request):
    req_filter = request.GET.get("filter").strip()
    if req_filter not in ["tracking_code", "customer", ""]:
        return

    if req_filter == "":
        req_filter = "customer"

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)
    query = request.GET.get("q", "").strip()

    packages = _search_packages_helper(query, per_page)
    page_obj = packages.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []

    return render(request, "packages/search.html", {"page_obj": page_obj,
                                                    "query": request.GET.get("q", ""),
                                                    "filter": req_filter,
                                                    "selected": selected,
                                                    "account_packages": True})
