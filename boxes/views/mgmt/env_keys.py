"""API keys and environment status page (read-only view of /etc/boxes.env)."""
from boxes.backend.setup_status import env_api_key_status
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def env_api_keys(request):
    """GET: dedicated page for environment/API key status (no secrets shown)."""
    return render(request, "mgmt/env_api_keys.html", {
        "env_api_keys": env_api_key_status(),
    })
