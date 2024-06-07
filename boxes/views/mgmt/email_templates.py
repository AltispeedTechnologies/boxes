from boxes.management.exception_catcher import exception_catcher
from boxes.models import EmailTemplate
from boxes.views.common import _clean_html
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def email_template(request):
    templates = EmailTemplate.objects.all().order_by("id")
    initial_content = templates.first().content
    subject = templates.first().subject
    return render(request, "mgmt/email_templates.html", {"templates": templates,
                                                         "subject": subject,
                                                         "initial_content": initial_content})


@require_http_methods(["POST"])
def add_email_template(request):
    template_name = request.POST.get("name")
    if template_name:
        new_template = EmailTemplate.objects.create(name=template_name, subject="", content="")
        return JsonResponse({"success": True, "id": new_template.id})


@require_http_methods(["GET"])
def email_template_content(request):
    template_id = request.GET.get("id")
    template = EmailTemplate.objects.get(id=template_id)
    return JsonResponse({"success": True,
                         "content": template.content,
                         "subject": template.subject})


@require_http_methods(["POST"])
@exception_catcher()
def update_email_template(request):
    template_id = request.POST.get("id")
    content = _clean_html(request.POST.get("content"))
    subject = request.POST.get("subject")

    template = EmailTemplate.objects.get(id=template_id)
    template.subject = subject
    template.content = content
    template.save()
