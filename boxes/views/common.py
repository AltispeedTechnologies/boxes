from boxes.models import *
from django.core.paginator import Paginator

PACKAGES_PER_PAGE = 10

def _get_packages(**kwargs):
    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related("account", "carrier", "packagetype", "packagepicklist").values(
        "id",
        "packagepicklist__picklist_id",
        "price",
        "carrier__name",
        "account__description",
        "package_type__description",
        "tracking_code",
        "comments",
    ).filter(**kwargs).order_by("id")

    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return paginator

def _search_packages_helper(request, **kwargs):
    filters = request.GET.get("filter", "").strip()
    allowed_filters = ["tracking_code", "customer"]
    if filters not in allowed_filters:
        raise ValueError("Invalid filter value")

    if filters == "tracking_code":
        query = request.GET.get("q", "").strip()
        packages = _get_packages(tracking_code__icontains=query, current_state=1, **kwargs)
    elif filters == "customer":
        account_id = request.GET.get("cid", "").strip()
        packages = _get_packages(account__id=account_id, current_state=1, **kwargs)
    
    return packages
