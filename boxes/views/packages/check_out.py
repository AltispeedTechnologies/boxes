from boxes.management.exception_catcher import exception_catcher
from boxes.views.packages.utility import update_packages_util
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
@exception_catcher()
def check_out_packages(request):
    result = update_packages_util(request, state=2, debit_credit_switch=True)
    if not result["success"]:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occured."])})


@require_http_methods(["POST"])
@exception_catcher()
def check_out_packages_reverse(request):
    result = update_packages_util(request, state=1, debit_credit_switch=False)
    if not result["success"]:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occured."])})
