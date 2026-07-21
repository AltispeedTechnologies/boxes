"""Staff JSON endpoint for management setup completeness (navbar refresh)."""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from boxes.backend.setup_status import compute_setup_status, invalidate_setup_status_cache


@require_http_methods(["GET"])
def mgmt_setup_status_api(request):
    """GET (staff): current setup flags for Management menu icons.

    Query ``?refresh=1`` forces cache invalidation then recompute.
    """
    if request.GET.get("refresh") in ("1", "true", "yes"):
        invalidate_setup_status_cache()
    status = compute_setup_status(use_cache=True)
    return JsonResponse({"success": True, "setup": status})
