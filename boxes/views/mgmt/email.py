import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import EmailSettings, EmailTemplate, GlobalSettings, NotificationRule, SentEmail
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def email_settings(request):
    templates = EmailTemplate.objects.all().order_by("id")
    global_settings, _ = GlobalSettings.objects.get_or_create(id=1)
    try:
        email_settings = EmailSettings.objects.latest("id")
    except EmailSettings.DoesNotExist:
        email_settings = None
    return render(request, "mgmt/email.html", {"templates": templates,
                                               "email_settings": email_settings,
                                               "email_sending": global_settings.email_sending,
                                               "view_type": "configure"})


@require_http_methods(["GET"])
def email_logs(request):
    emails = SentEmail.objects.annotate(
        sent_id=F("pk"),
        timestamp_val=F("timestamp"),
        subject_val=F("subject"),
        email_val=F("email"),
        status=F("success"),
        tracking_codes=ArrayAgg(
            Concat(
                F("sentemailpackage__package__id"),
                Value(" "),
                F("sentemailpackage__package__tracking_code"),
                output_field=CharField()
            ),
            distinct=True,
            filter=Q(sentemailpackage__package__isnull=False)
        )
    ).order_by("-timestamp_val")
    for email in emails:
        tracking_codes = [
            [int(part) if i == 0 else part for i, part in enumerate(code.split(" ", 1))]
            for code in email.tracking_codes
        ]
        email.tracking_codes = tracking_codes

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(emails, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, "mgmt/email_logs.html", {"page_obj": page_obj,
                                                    "enable_tracking_codes": True,
                                                    "view_type": "logs"})


@require_http_methods(["POST"])
@exception_catcher()
def save_email_settings(request):
    data = json.loads(request.body)
    email_sending = bool(data.get("email_sending"))
    sender_name = data.get("sender_name")
    sender_email = data.get("sender_email")
    check_in_template_id = data.get("check_in_template")

    with transaction.atomic():
        # Update global settings for sending emails
        settings, _ = GlobalSettings.objects.get_or_create(id=1)
        settings.email_sending = email_sending
        settings.save()

        # Create or update the main email settings
        EmailSettings.objects.all().delete()
        email_settings = EmailSettings.objects.create(
            sender_name=sender_name,
            sender_email=sender_email,
            check_in_template_id=check_in_template_id
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
