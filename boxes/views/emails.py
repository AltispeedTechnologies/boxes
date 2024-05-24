from boxes.models import SentEmailContents
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def get_email_contents(request, pk):
    contents = SentEmailContents.objects.filter(
        sent_email_id=pk).values_list(
        "html", flat=True).first()

    return JsonResponse({"contents": contents})
