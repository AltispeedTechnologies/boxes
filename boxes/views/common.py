from boxes.models import *
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery

PACKAGES_PER_PAGE = 10

def _get_packages(**kwargs):
    check_in_subquery = PackageLedger.objects.filter(
        package_id=OuterRef("pk"),
        state=1
    ).order_by("-timestamp").values("timestamp")[:1]

    check_out_subquery = PackageLedger.objects.filter(
        package_id=OuterRef("pk"),
        state=2
    ).order_by("-timestamp").values("timestamp")[:1]

    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related(
        "account", "carrier", "packagetype", "packagepicklist"
    ).annotate(
        check_in_time=Subquery(check_in_subquery),
        check_out_time=Subquery(check_out_subquery)
    ).values(
        "id",
        "packagepicklist__picklist_id",
        "price",
        "carrier__name",
        "account__description",
        "package_type__description",
        "tracking_code",
        "comments",
        "check_in_time",
        "check_out_time"
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
