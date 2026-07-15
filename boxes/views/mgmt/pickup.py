"""Staff CRUD for pickup days and schedule rules."""
import json
from datetime import date, datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from boxes.backend.pickup import (
    list_open_pickup_dates,
    set_pickup_day_active,
)
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Picklist, PickupDay, PickupScheduleRule


def _parse_date(value):
    """Parse YYYY-MM-DD or MM/DD/YYYY into a date."""
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date: {value}")


@require_http_methods(["GET"])
def pickup_mgmt(request):
    """GET: staff pickup days and schedule rules management page."""
    today = date.today()
    days = (
        PickupDay.objects.filter(date__gte=today - timedelta(days=7))
        .select_related("picklist")
        .order_by("date")
    )
    rules = PickupScheduleRule.objects.all().order_by("name")
    picklists = Picklist.objects.all().order_by("-date", "id")
    open_dates = list_open_pickup_dates(today, today + timedelta(days=60))
    return render(
        request,
        "mgmt/pickup.html",
        {
            "days": days,
            "rules": rules,
            "picklists": picklists,
            "open_dates": open_dates,
            "weekday_labels": [
                (0, "Monday"),
                (1, "Tuesday"),
                (2, "Wednesday"),
                (3, "Thursday"),
                (4, "Friday"),
                (5, "Saturday"),
                (6, "Sunday"),
            ],
        },
    )


@require_http_methods(["GET"])
def pickup_open_days(request):
    """GET: JSON open pickup dates in a window (start/end query params)."""
    today = date.today()
    start = _parse_date(request.GET.get("start")) or today
    end = _parse_date(request.GET.get("end")) or (today + timedelta(days=60))
    if end < start:
        raise ValueError("end before start")
    dates = list_open_pickup_dates(start, end)
    return JsonResponse({
        "success": True,
        "dates": [d.isoformat() for d in dates],
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_pickup_rules(request):
    """POST: create/update/delete schedule rules from JSON payload."""
    data = json.loads(request.body)
    deleted_ids = data.get("deleted", []) or []
    if deleted_ids:
        PickupScheduleRule.objects.filter(id__in=[int(i) for i in deleted_ids]).delete()

    updated = {}
    for rule_id, attrs in (data.get("rules") or data).items():
        if rule_id in ("deleted",):
            continue
        if not isinstance(attrs, dict):
            continue
        name = (attrs.get("name") or "").strip()
        recurrence = attrs.get("recurrence") or PickupScheduleRule.RECURRENCE_NONE
        weekday = attrs.get("weekday")
        if weekday in ("", None):
            weekday = None
        else:
            weekday = int(weekday)
        start_date = _parse_date(attrs.get("start_date"))
        end_date = _parse_date(attrs.get("end_date"))
        is_active = bool(attrs.get("is_active", True))
        if not name or not start_date:
            raise ValueError("name and start_date required")
        if recurrence == PickupScheduleRule.RECURRENCE_WEEKLY and weekday is None:
            raise ValueError("weekday required for weekly rules")

        if str(rule_id).startswith("NEW_"):
            rule = PickupScheduleRule.objects.create(
                name=name,
                recurrence=recurrence,
                weekday=weekday,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
            )
            updated[rule_id] = rule.id
        else:
            rule = PickupScheduleRule.objects.get(id=int(rule_id))
            rule.name = name
            rule.recurrence = recurrence
            rule.weekday = weekday
            rule.start_date = start_date
            rule.end_date = end_date
            rule.is_active = is_active
            rule.save()
            updated[str(rule.id)] = rule.id

    return JsonResponse({"success": True, "updated_rules": updated})


@require_http_methods(["POST"])
@exception_catcher()
def update_pickup_days(request):
    """POST: create/update pickup days (date, is_active, notes, picklist)."""
    data = json.loads(request.body)
    deleted_ids = data.get("deleted", []) or []
    if deleted_ids:
        PickupDay.objects.filter(id__in=[int(i) for i in deleted_ids]).delete()

    updated = {}
    items = data.get("days") or data
    for day_id, attrs in items.items():
        if day_id in ("deleted", "days"):
            continue
        if not isinstance(attrs, dict):
            continue
        day_date = _parse_date(attrs.get("date"))
        notes = attrs.get("notes") or None
        is_active = attrs.get("is_active")
        picklist_id = attrs.get("picklist_id")
        if picklist_id in ("", None):
            picklist_id = None
        else:
            picklist_id = int(picklist_id)
            get_object_or_404(Picklist, pk=picklist_id)

        if str(day_id).startswith("NEW_"):
            if not day_date:
                raise ValueError("date required")
            day = PickupDay.objects.create(
                date=day_date,
                is_active=True if is_active is None else bool(is_active),
                notes=notes,
                picklist_id=picklist_id,
            )
            updated[day_id] = day.id
        else:
            day = PickupDay.objects.get(id=int(day_id))
            if day_date is not None:
                day.date = day_date
            if notes is not None:
                day.notes = notes
            if picklist_id is not None or "picklist_id" in attrs:
                day.picklist_id = picklist_id
            changing_active = (
                is_active is not None and bool(is_active) != day.is_active
            )
            day.save()
            if changing_active:
                set_pickup_day_active(day, bool(is_active))
            updated[str(day.id)] = day.id

    return JsonResponse({"success": True, "updated_days": updated})
