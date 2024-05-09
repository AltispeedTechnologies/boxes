import decimal
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import AccountChargeSettings, EmailTemplate, EmailSettings, NotificationRule, PackageType
from .common import _clean_html

@require_http_methods(["GET"])
def charge_settings(request):
    charge_rules = AccountChargeSettings.objects.filter(
        package_type_id__isnull=True, 
        price__isnull=True, 
        frequency__isnull=True,
        endpoint__isnull=True
    ).order_by("days")

    custom_charge_rules = AccountChargeSettings.objects.filter(
        package_type_id__isnull=False, 
        price__isnull=False, 
        frequency__isnull=False,
        endpoint__isnull=True
    ).order_by("days")

    endpoint = AccountChargeSettings.objects.filter(
        endpoint__isnull=False
    ).values_list("endpoint", flat=True).first()

    package_types = PackageType.objects.all().values("id", "description")
    return render(request, "mgmt/charges.html", {"charge_rules": charge_rules,
                                                 "custom_charge_rules": custom_charge_rules,
                                                 "endpoint": endpoint,
                                                 "package_types": package_types})

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
    subject = templates.first().subject
    return render(request, "mgmt/email_templates.html", {"templates": templates,
                                                         "subject": subject,
                                                         "initial_content": initial_content})

@require_http_methods(["GET"])
def email_template_content(request):
    template_id = request.GET.get("id")
    template = EmailTemplate.objects.get(id=template_id)
    return JsonResponse({"content": template.content,
                         "subject": template.subject})

@require_http_methods(["POST"])
def add_email_template(request):
    template_name = request.POST.get("name")
    if template_name:
        new_template = EmailTemplate.objects.create(name=template_name, subject="", content="")
        return JsonResponse({"id": new_template.id})

@require_http_methods(["POST"])
def update_email_template(request):
    template_id = request.POST.get("id")
    print(request.POST.get("content"))
    content = _clean_html(request.POST.get("content"))
    print(content)
    subject = request.POST.get("subject")
    try:
        template = EmailTemplate.objects.get(id=template_id)
        template.subject = subject
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

@require_http_methods(["POST"])
def save_charge_settings(request):
    data = json.loads(request.body)

    AccountChargeSettings.objects.all().delete()
    for rule in data:
        package_type_id = rule.get("package_type_id")
        days = rule.get("days")
        price = rule.get("price")
        frequency = rule.get("frequency")
        endpoint = rule.get("endpoint")

        AccountChargeSettings.objects.create(
            package_type_id=package_type_id,
            days=int(days) if days else None,
            price=decimal.Decimal(price) if price else None,
            frequency=frequency,
            endpoint=int(endpoint) if endpoint else None
        )

    return JsonResponse({"success": True})
