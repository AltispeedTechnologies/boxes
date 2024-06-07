import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Carrier
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def carrier_settings(request):
    carriers = Carrier.objects.all().order_by("id")
    return render(request, "mgmt/carriers.html", {"carriers": carriers})


@require_http_methods(["POST"])
@exception_catcher()
def update_carriers(request):
    data = json.loads(request.body)
    updated_carriers = {}

    for carrier_id, attributes in data.items():
        if str(carrier_id).startswith("NEW_"):
            new_carrier = Carrier(name=attributes["name"],
                                  phone_number=attributes["phone_number"],
                                  website=attributes["website"])
            new_carrier.save()
            updated_carriers[carrier_id] = new_carrier.id
        else:
            carrier = Carrier.objects.get(id=int(carrier_id))
            if carrier.name != attributes["name"]:
                carrier.name = attributes["name"]
            carrier.phone_number = attributes["phone_number"]
            carrier.website = attributes["website"]
            carrier.save()

    return JsonResponse({"success": True, "updated_carriers": updated_carriers})
