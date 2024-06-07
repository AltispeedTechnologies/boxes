import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import PackageType
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def package_type_settings(request):
    package_types = PackageType.objects.all().order_by("id")
    return render(request, "mgmt/types.html", {"package_types": package_types})


@require_http_methods(["POST"])
@exception_catcher()
def update_package_types(request):
    data = json.loads(request.body)
    updated_types = {}

    for type_id, attributes in data.items():
        if str(type_id).startswith("NEW_"):
            new_type = PackageType(shortcode=attributes["shortcode"],
                                   description=attributes["description"],
                                   default_price=attributes["default_price"])
            new_type.save()
            updated_types[type_id] = new_type.id
        else:
            try:
                package_type = PackageType.objects.get(id=int(type_id))
                package_type.shortcode = attributes["shortcode"]
                package_type.description = attributes["description"]
                package_type.default_price = attributes["default_price"]
                package_type.save()
            except PackageType.DoesNotExist:
                updated_types[type_id] = "Not found"

    return JsonResponse({"success": True, "updated_types": updated_types})
