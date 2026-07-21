"""Email template CRUD for staff."""
from boxes.management.exception_catcher import exception_catcher
from boxes.models import EmailTemplate
from boxes.views.common import _clean_html
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from boxes.backend.setup_status import invalidate_setup_status_cache


@require_http_methods(["GET"])
def email_template(request):
    """GET: template list/editor page."""
    templates = EmailTemplate.objects.all().order_by("id")
    first = templates.first()
    initial_content = first.content if first else ""
    subject = first.subject if first else ""
    return render(request, "mgmt/email_templates.html", {
        "templates": templates,
        "subject": subject,
        "initial_content": initial_content,
    })


@require_http_methods(["POST"])
def add_email_template(request):
    """POST: create a new EmailTemplate."""
    template_name = (request.POST.get("name") or "").strip()
    if not template_name:
        return JsonResponse({"success": False, "errors": ["Template name is required"]})
    new_template = EmailTemplate.objects.create(name=template_name, subject="", content="")
    invalidate_setup_status_cache()
    return JsonResponse({"success": True, "id": new_template.id})


@require_http_methods(["GET"])
def email_template_content(request):
    """GET: fetch subject/body for a template id."""
    template_id = request.GET.get("id")
    if not template_id:
        return JsonResponse({"success": False, "errors": ["Template id is required"]})
    try:
        template = EmailTemplate.objects.get(id=template_id)
    except (EmailTemplate.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"success": False, "errors": ["Template not found"]})
    return JsonResponse({
        "success": True,
        "content": template.content,
        "subject": template.subject,
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_email_template(request):
    """POST: update template name/subject/content."""
    template_id = request.POST.get("id")
    if not template_id:
        return JsonResponse({"success": False, "errors": ["Template id is required"]})
    content = _clean_html(request.POST.get("content") or "")
    subject = request.POST.get("subject") or ""

    template = EmailTemplate.objects.get(id=template_id)
    template.subject = subject
    template.content = content
    template.save()
