from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from boxes.models import Carrier


@require_http_methods(["GET"])
def carrier_search(request):
    search_query = request.GET.get("term", "")
    carriers = Carrier.objects.filter(name__icontains=search_query)[:10]
    results = [{"id": carrier.id, "text": carrier.name} for carrier in carriers]
    return JsonResponse({"results": results})
