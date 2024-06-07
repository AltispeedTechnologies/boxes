import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import PackageQueue, PackageType, Queue
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def type_search(request):
    search_query = request.GET.get("term", "")
    pkgtypes = PackageType.objects.filter(description__icontains=search_query)[:10]
    results = [{"id": pkgtype.id,
                "text": pkgtype.description,
                "default_price": pkgtype.default_price} for pkgtype in pkgtypes]
    return JsonResponse({"success": True, "results": results})


@require_http_methods(["GET"])
def queue_packages(request, pk):
    packages = PackageQueue.objects.filter(queue=pk).select_related(
        "package__account",
        "package__package_type",
        "package__carrier"
    ).annotate(
        account=F("package__account__name"),
        account_id=F("package__account__id"),
        tracking_code=F("package__tracking_code"),
        price=F("package__price"),
        carrier=F("package__carrier__name"),
        carrier_id=F("package__carrier__id"),
        package_type=F("package__package_type__description"),
        package_type_id=F("package__package_type__id"),
        inside=F("package__inside"),
        comments=F("package__comments")
    ).values(
        "package_id",
        "account",
        "account_id",
        "tracking_code",
        "price",
        "carrier",
        "carrier_id",
        "package_type",
        "package_type_id",
        "inside",
        "comments"
    )

    return JsonResponse({"success": True, "packages": list(packages)})


@require_http_methods(["POST"])
@exception_catcher()
def update_queue_name(request, pk):
    data = json.loads(request.body)
    queue_id = data["id"]
    description = data["description"]

    queue = get_object_or_404(Queue, pk=queue_id)

    queue.description = description
    queue.save()
