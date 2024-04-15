from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from boxes.models import Account

@require_http_methods(["GET"])
def account_search(request):
    search_query = request.GET.get("term", "")
    accounts = Account.objects.filter(description__icontains=search_query)[:10]
    results = [{"id": account.id, "text": account.description} for account in accounts]
    return JsonResponse({"results": results})
