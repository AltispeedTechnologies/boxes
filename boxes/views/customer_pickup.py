"""Customer pickup reservation endpoints."""
import json
from datetime import date, datetime, timedelta

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from boxes.backend.membership import get_active_account, list_accounts_for_user
from boxes.backend.pickup import get_or_create_open_pickup_day, list_open_pickup_dates
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Package, PackagePickupReservation


@require_http_methods(["GET"])
def customer_open_pickup_days(request):
    """GET: JSON open pickup dates for the customer reservation UI."""
    today = date.today()
    dates = list_open_pickup_dates(today, today + timedelta(days=60))
    return JsonResponse({
        "success": True,
        "dates": [d.isoformat() for d in dates],
    })


@require_http_methods(["POST"])
@exception_catcher()
def customer_reserve_pickup(request):
    """POST: reserve selected packages for an open pickup day.

    Body JSON: package_ids list and date YYYY-MM-DD.
    Packages must belong to the **active** customer account and be checked-in (state 1).
    Authorization (account scope) runs before pickup-day creation.
    """
    data = json.loads(request.body) if request.body else {}
    package_ids = data.get("package_ids") or data.get("ids") or []
    package_ids = [int(x) for x in package_ids]
    if not package_ids:
        raise ValueError("No packages selected")

    account = get_active_account(request)
    if account is None:
        accounts = list(list_accounts_for_user(request.user))
        if not accounts:
            return JsonResponse(
                {"success": False, "errors": ["No linked accounts."]},
                status=400,
            )
        return JsonResponse(
            {
                "success": False,
                "errors": ["Select an account first."],
                "redirect": "/customer/select-account",
            },
            status=400,
        )

    packages = list(
        Package.objects.filter(
            id__in=package_ids,
            account_id=account.id,
            current_state=1,
        )
    )
    found_ids = {p.id for p in packages}
    missing = set(package_ids) - found_ids
    if missing:
        raise PermissionDenied("Packages not available for reservation.")

    date_str = data.get("date")
    if not date_str:
        raise ValueError("date required")
    target = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
    pickup_day = get_or_create_open_pickup_day(target)

    created = 0
    updated = 0
    for package in packages:
        _reservation, was_created = PackagePickupReservation.objects.update_or_create(
            package=package,
            defaults={
                "pickup_day": pickup_day,
                "user": request.user,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return JsonResponse({
        "success": True,
        "created": created,
        "updated": updated,
        "pickup_day_id": pickup_day.id,
        "date": pickup_day.date.isoformat(),
        "account_id": account.id,
    })
