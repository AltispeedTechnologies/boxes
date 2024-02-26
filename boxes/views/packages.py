import re
from boxes.forms import PackageForm
from boxes.models import Package, Carrier, Account, PACKAGE_STATES
from django.shortcuts import render
from django.contrib import messages
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect

# Reverse the PACKAGE_STATES tuple to create a mapping from state names to IDs
STATE_NAME_TO_ID_MAP = dict((name, id) for id, name in PACKAGE_STATES if id != 0)
CONTEXT = {"STATE_NAMES": STATE_NAME_TO_ID_MAP}

def all_packages(request):
    packages = _get_packages(current_state__gt = 0)
    return render(request, "packages/index.html", {"packages": packages, **CONTEXT})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.POST)
        print(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.carrier_id = form.cleaned_data["carrier_id"]
            package.account_id = form.cleaned_data["account_id"]
            package.package_type_id = form.cleaned_data["package_type_id"]
            package.save()
            return JsonResponse({"success": True})
        else:
            errors = dict(form.errors.items()) if form.errors else {}
            return JsonResponse({"success": False, "errors": errors})  # Return error response with form errors
    else:
        form = PackageForm()
        return render(request, "packages/create.html", {"form": form})

def search_packages(request):
    query = request.GET.get("q", "").strip()
    state = request.GET.get("state", "").strip()
    filters = request.GET.get("filter", "").strip()

    allowed_filters = ["tracking_code", "current_state", "customer"]
    if filters not in allowed_filters:
        messages.error(request, "Invalid filter value")
        return redirect("packages")

    query = re.sub(r"[^\w\s-]", "", query)

    if filters == "tracking_code":
        packages = search_by_tracking_code(query)
    elif filters == "customer":
        packages = _get_packages(account__description__startswith = query)
    elif filters == "current_state":
        packages = search_by_current_state(request, state)

    return render(request, "packages/search.html", {"packages": packages, "query": query, "filter": filters, **CONTEXT})

def search_by_tracking_code(query):
    packages = _get_packages(tracking_code__icontains=query)
    return packages

def search_by_current_state(request, query):
    # Remove leading and trailing whitespace from the query string value
    selected_state_name = query.strip()
    
    # Find matching states with flexible whitespace handling
    matching_states = [state_name.strip() for state_name in STATE_NAME_TO_ID_MAP.keys() if selected_state_name in state_name]
    
    if matching_states:
        # Get the corresponding IDs for the matching state names
        matching_state_ids = [STATE_NAME_TO_ID_MAP[state_name] for state_name in matching_states]
        packages = _get_packages(current_state__in=matching_state_ids)
        return packages
    else:
        messages.error(request, "Invalid state name")
        return redirect("packages")

def _get_packages(**kwargs):
    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related("account", "carrier", "packagetype").values(
        "id",
        "current_state",
        "package_type__shortcode",
        "price",
        "carrier__name",
        "account__description",
        "package_type__description",
        "tracking_code",
        "comments",
    ).filter(**kwargs)
    _add_current_state_display(packages)
    return packages

def _add_current_state_display(packages):
    for package in packages:
        package["current_state_display"] = dict(PACKAGE_STATES)[package["current_state"]]
