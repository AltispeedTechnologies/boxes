"""Customer pickup reservation endpoints."""
import json
from datetime import date, datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from boxes.backend.pickup import get_or_create_open_pickup_day, list_open_pickup_dates
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Package, PackagePickupReservation, UserAccount


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
    Packages must belong to the user account and be checked-in (state 1).
    Existing reservations for those packages are moved to the new day.
    """
    data = json.loads(request.body)
    package_ids = data.get("package_ids") or data.get("ids") or []
    package_ids = [int(x) for x in package_ids]
    if not package_ids:
        raise ValueError("No packages selected")

    date_str = data.get("date")
    if not date_str:
        raise ValueError("date required")
    target = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
    pickup_day = get_or_create_open_pickup_day(target)

    account_id = UserAccount.objects.get(user_id=request.user.id).account_id
    packages = list(
        Package.objects.filter(
            id__in=package_ids,
            account_id=account_id,
            current_state=1,
        )
    )
    found_ids = {p.id for p in packages}
    missing = set(package_ids) - found_ids
    if missing:
        raise RuntimeError(
            "Packages not available for reservation: %s" % sorted(missing)
        )

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
    })
