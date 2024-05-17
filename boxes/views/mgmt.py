import decimal
import json
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import AccountChargeSettings, Carrier, EmailTemplate, EmailSettings, NotificationRule, PackageType
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

@require_http_methods(["GET"])
def package_type_settings(request):
    package_types = PackageType.objects.all().order_by("id")
    return render(request, "mgmt/types.html", {"package_types": package_types})

@require_http_methods(["POST"])
def update_package_types(request):
    try:
        data = json.loads(request.body)
        updated_types = {}

        for type_id, attributes in data.items():
            if str(type_id).startswith("NEW_"):
                new_type = PackageType(shortcode=attributes["shortcode"],
                                       description=attributes["description"],
                                       default_price=attributes["default_price"])
                new_type.save()
                updated_types[type_id] = new_type.id
            else:
                try:
                    package_type = PackageType.objects.get(id=int(type_id))
                    package_type.shortcode = attributes["shortcode"]
                    package_type.description = attributes["description"]
                    package_type.default_price = attributes["default_price"]
                    package_type.save()
                except PackageType.DoesNotExist:
                    updated_types[type_id] = "Not found"

        return JsonResponse({"success": True, "updated_types": updated_types})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "errors": "Invalid JSON"})
    except Exception as e:
        return JsonResponse({"success": False, "errors": str(e)})

@require_http_methods(["GET"])
def carrier_settings(request):
    carriers = Carrier.objects.all().order_by("id")
    return render(request, "mgmt/carriers.html", {"carriers": carriers})

@require_http_methods(["POST"])
def update_carriers(request):
    try:
        data = json.loads(request.body)
        print(data)
        updated_carriers = {}

        for carrier_id, attributes in data.items():
            if str(carrier_id).startswith("NEW_"):
                new_carrier = Carrier(name=attributes["name"],
                                      phone_number=attributes["phone_number"],
                                      website=attributes["website"])
                new_carrier.save()
                updated_carriers[carrier_id] = new_carrier.id
            else:
                try:
                    carrier = Carrier.objects.get(id=int(carrier_id))
                    if carrier.name != attributes["name"]:
                        carrier.name = attributes["name"]
                    carrier.phone_number = attributes["phone_number"]
                    carrier.website = attributes["website"]
                    carrier.save()
                except PackageType.DoesNotExist:
                    updated_carriers[carrier_id] = "Not found"

        return JsonResponse({"success": True, "updated_carriers": updated_carriers})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "errors": "Invalid JSON"})
    except Exception as e:
        return JsonResponse({"success": False, "errors": str(e)})
