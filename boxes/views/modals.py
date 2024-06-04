from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def get_bulk_modals(request):
    return render(request, "modals/bulk.html")


@require_http_methods(["GET"])
def get_actions_modals(request):
    return render(request, "modals/actions.html")


@require_http_methods(["GET"])
def get_picklist_mgmt_modals(request):
    return render(request, "modals/picklist_mgmt.html")
