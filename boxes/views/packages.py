from boxes.forms import PackageForm
from django.contrib import messages
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from boxes.models import Address, Package, PACKAGE_STATES

# Reverse the PACKAGE_STATES tuple to create a mapping from state names to IDs
STATE_NAME_TO_ID_MAP = dict((name, id) for id, name in PACKAGE_STATES)

def all_packages(request):
    packages = Package.objects.all()
    return render(request, "packages/index.html", {"packages": packages})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.user, request.POST)
        if form.is_valid():
            # Process the form data and save the new package
            package = form.save(commit=False)
            package.user_id = request.user.id
            package.account_id_id = 1
            package.address_id_id = 1
            package.save()

            return redirect("packages")
    else:
        form = PackageForm(request.user)

    return render(request, "packages/create.html", {"form": form})

def search_packages(request):
    query = request.GET.get("q", "").strip()
    filters = request.GET.get("filter", "").strip()

    allowed_filters = ["tracking_code", "current_state"]
    if filters not in allowed_filters:
        messages.error(request, "Invalid filter value")
        return redirect("packages")

    try:
        validate_slug(query)
    except ValidationError:
        messages.error(request, "Invalid query value")
        return redirect("packages")

    if filters == "tracking_code":
        # Find all packages containing this tracking code
        packages = Package.objects.filter(tracking_code__icontains=query)
    elif filters == "current_state":
        # Convert human-readable state to its corresponding ID
        matching_states = [state_id for name, state_id in STATE_NAME_TO_ID_MAP.items() if query.lower() in name.lower()]

        if matching_states:
            packages = Package.objects.filter(current_state__in=matching_states)
        else:
            messages.error(request, "Invalid state name")
            return redirect("packages")

    return render(request, "packages/search.html", {"packages": packages, "query": query, "filter": filters})
