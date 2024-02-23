import re
from django.shortcuts import render
from boxes.forms import PackageForm
from django.contrib import messages
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from boxes.models import Package, PACKAGE_STATES

# Reverse the PACKAGE_STATES tuple to create a mapping from state names to IDs
STATE_NAME_TO_ID_MAP = dict((name, id) for id, name in PACKAGE_STATES)
CONTEXT = {"STATE_NAMES": STATE_NAME_TO_ID_MAP}

def all_packages(request):
    packages = _get_packages()
    return render(request, "packages/index.html", {"packages": packages, **CONTEXT})

def create_package(request):
    form = PackageForm(request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        package = form.save(commit=False)
        package.user = request.user.id
        package.account_id = 1
        package.address_id = 1
        package.current_state = 2
        package.save()
        #return redirect("packages")
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
    packages = Package.objects.select_related("account", "address").values(
        "id",
        "account__description",
        "address__address",
        "tracking_code",
        "current_state",
    ).filter(**kwargs)
    _add_current_state_display(packages)
    return packages

def _add_current_state_display(packages):
    for package in packages:
        package["current_state_display"] = dict(PACKAGE_STATES)[package["current_state"]]
