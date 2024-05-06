import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import EmailTemplate, EmailSettings, NotificationRule
from .common import _clean_html

@require_http_methods(["GET"])
def email_settings(request):
    templates = EmailTemplate.objects.all().order_by("id")
    try:
        email_settings = EmailSettings.objects.latest("id")
    except EmailSettings.DoesNotExist:
        email_settings = None
    return render(request, "mgmt/email.html", {"templates": templates,
                                               "email_settings": email_settings})

@require_http_methods(["GET"])
def email_template(request):
    templates = EmailTemplate.objects.all().order_by("id")
    initial_content = templates.first().content
    return render(request, "mgmt/email_templates.html", {"templates": templates,
                                                         "initial_content": initial_content})

@require_http_methods(["GET"])
def email_template_content(request):
    template_id = request.GET.get("id")
    template = EmailTemplate.objects.get(id=template_id)
    return JsonResponse({"content": template.content})

@require_http_methods(["POST"])
def update_email_template(request):
    template_id = request.POST.get("id")
    print(request.POST.get("content"))
    content = _clean_html(request.POST.get("content"))
    print(content)
    try:
        template = EmailTemplate.objects.get(id=template_id)
        template.content = content
        template.save()
        return JsonResponse({"status": "success", "message": "Template updated successfully."})
    except EmailTemplate.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Template not found."}, status=404)

@require_http_methods(["POST"])
def save_email_settings(request):
    data = json.loads(request.body)
    sender_name = data.get("sender_name")
    sender_email = data.get("sender_email")
    check_in_template_id = data.get("check_in_template")
    
    # Create or update the main email settings
    email_settings, created = EmailSettings.objects.update_or_create(
        sender_name=sender_name,
        sender_email=sender_email,
        defaults={"check_in_template_id": check_in_template_id}
    )
    
    # Handle notification rules
    NotificationRule.objects.filter(email_settings=email_settings).delete()
    for rule in data.get("notification_rules", []):
        days = rule.get("days")
        template_id = rule.get("template_id")
        NotificationRule.objects.create(
            email_settings=email_settings,
            days=days,
            template_id=template_id
        )
    
    return JsonResponse({"status": "success", "message": "Email settings updated."})
