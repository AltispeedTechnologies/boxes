from boxes.models import SentEmail, SentEmailContents
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def get_email_contents(request, pk):
    subject = SentEmail.objects.filter(pk=pk).values_list("subject", flat=True).first()

    contents = SentEmailContents.objects.filter(
        sent_email_id=pk).values_list(
        "html", flat=True).first()

    return JsonResponse({"contents": contents, "subject": subject})
