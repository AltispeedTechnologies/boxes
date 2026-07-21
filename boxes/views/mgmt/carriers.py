"""Carrier catalog management."""
import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Carrier
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from boxes.backend.setup_status import invalidate_setup_status_cache


@require_http_methods(["GET"])
def carrier_settings(request):
    """GET: carriers management page."""
    carriers = Carrier.objects.all().order_by("id")
    return render(request, "mgmt/carriers.html", {"carriers": carriers})


@require_http_methods(["POST"])
@exception_catcher()
def update_carriers(request):
    """POST: create/update carriers from inline form data."""
    data = json.loads(request.body)
    if not isinstance(data, dict):
        return JsonResponse({"success": False, "errors": ["Invalid payload"]})

    updated_carriers = {}
    errors = []

    for carrier_id, attributes in data.items():
        if not isinstance(attributes, dict):
            errors.append(f"Invalid row {carrier_id}")
            continue
        name = (attributes.get("name") or "").strip()
        if not name:
            errors.append(f"Carrier name is required (row {carrier_id})")
            continue
        phone_number = (attributes.get("phone_number") or "").strip()
        website = (attributes.get("website") or "").strip()
        is_active = bool(attributes.get("is_active", True))
        allow_duplicate_tracking = bool(attributes.get("allow_duplicate_tracking", False))

        if str(carrier_id).startswith("NEW_"):
            new_carrier = Carrier(
                name=name[:32],
                phone_number=phone_number[:15],
                website=website[:32],
                is_active=is_active,
                allow_duplicate_tracking=allow_duplicate_tracking,
            )
            new_carrier.save()
            updated_carriers[carrier_id] = new_carrier.id
        else:
            try:
                carrier = Carrier.objects.get(id=int(carrier_id))
            except (Carrier.DoesNotExist, ValueError, TypeError):
                errors.append(f"Carrier {carrier_id} not found")
                continue
            carrier.name = name[:32]
            carrier.phone_number = phone_number[:15]
            carrier.website = website[:32]
            carrier.is_active = is_active
            carrier.allow_duplicate_tracking = allow_duplicate_tracking
            carrier.save()

    if errors:
        return JsonResponse({"success": False, "errors": errors})

    invalidate_setup_status_cache()
    return JsonResponse({"success": True, "updated_carriers": updated_carriers})
