import os
import json
import re
from boxes.models import (
    CustomUserEmail, EmailQueue, EmailSettings, GlobalSettings, Package, SentEmail,
    SentEmailContents, SentEmailPackage, SentEmailResult, UserAccount
)
from celery import shared_task
from django.db import transaction
from html import unescape
from mailjet_rest import Client


def _fetch_candidates():
    candidates = {}
    template_objs = {}

    with transaction.atomic():
        queue_items = list(EmailQueue.objects.select_for_update().select_related("package__account", "template").all())
        for item in queue_items:
            account_id = item.package.account.id
            package_id = item.package.id
            template = item.template

            if account_id not in candidates:
                candidates[account_id] = {}
            if template.id not in candidates[account_id]:
                candidates[account_id][template.id] = []
                template_objs[template.id] = template
            candidates[account_id][template.id].append(package_id)

            item.delete()

    return candidates, template_objs


def _send_email(email_data):
    email_payload = {
        "Messages": [
            {
                "From": {"Email": email_data["email_settings"].sender_email,
                         "Name": email_data["email_settings"].sender_name},
                "To": [{"Email": email_data["recipient_email"], "Name": email_data["hr_name"]}],
                "Subject": email_data["template"].subject,
                "TextPart": email_data["email_text"],
                "HTMLPart": email_data["email_html"]
            }
        ]
    }

    # Send the email
    result = email_data["mailjet"].send.create(data=email_payload)

    # Interpret the immediate result and store it for later analysis
    json_result = result.json()
    json_message = json_result["Messages"][0]
    success = json_message["Status"] == "success"
    message_uuid = json_message["To"][0]["MessageUUID"] if success else None

    # Create main SentEmail object
    sent_email = SentEmail.objects.create(
        account_id=email_data["account_id"],
        subject=email_data["template"].subject,
        email=email_data["recipient_email"],
        success=success,
        message_uuid=message_uuid
    )
    # Store the contents of the sent email
    SentEmailContents.objects.create(sent_email=sent_email, html=email_data["email_html"])
    # Ensure each package can have a record of a sent email
    for package_id in email_data["package_ids"]:
        SentEmailPackage.objects.create(sent_email=sent_email, package_id=package_id)
    # Store the raw JSON result, in case something goes haywire
    SentEmailResult.objects.create(sent_email=sent_email, response=json_result)


def _prepare_email_content(user, template, tracking_code, carrier_name):
    hr_name = f"{user.first_name} {user.last_name}"
    email_html = template.content

    pattern = r'<span [^>]*class="custom-block[^"]*"[^>]*>([^<]+)</span>'
    email_html = re.sub(pattern, lambda m: f'{{{m.group(1).lower().replace(" ", "_")}}}', email_html)
    email_html = email_html.format(first_name=user.first_name, last_name=user.last_name, tracking_code=tracking_code,
                                   carrier=carrier_name)

    # Remove all HTML tags and replace <br> and <br/> with newlines
    email_text = re.sub(r"<[^>]+>", "", email_html)
    email_text = re.sub(r"<br\s*/?>", "\n", email_text, flags=re.IGNORECASE)
    email_text = unescape(email_text)

    return hr_name, email_html, email_text


def _send_users(users, email_data):
    for user in users:
        hr_name, email_html, email_text = _prepare_email_content(user, email_data["template"],
                                                                 email_data["tracking_code"],
                                                                 email_data["carrier_name"])

        for recipient_email_obj in CustomUserEmail.objects.filter(user=user):
            email_data.update({
                "hr_name": hr_name,
                "email_html": email_html,
                "email_text": email_text,
                "recipient_email": recipient_email_obj.email,
            })
            _send_email(email_data)


@shared_task
def send_emails():
    # Do not proceed if email sending is disabled
    global_settings, _ = GlobalSettings.objects.get_or_create(id=1)
    if not global_settings.email_sending:
        return

    candidates, template_objs = _fetch_candidates()
    email_settings = EmailSettings.objects.first()

    api_key = os.environ["MJ_APIKEY_PUBLIC"]
    api_secret = os.environ["MJ_APIKEY_PRIVATE"]
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")

    for account_id, templates in candidates.items():
        user_accounts = UserAccount.objects.filter(account__id=account_id)
        users = [user_account.user for user_account in user_accounts]

        for template_id, package_ids in templates.items():
            template = template_objs[template_id]
            results = Package.objects.filter(pk__in=package_ids).values_list("tracking_code", "carrier__name")

            if results:
                tracking_codes = [result[0] for result in results]
                carrier_names = [result[1] for result in results]

                tracking_code = ", ".join(tracking_codes)
                carrier_name = ", ".join(set(carrier_names))

                email_data = {
                    "template": template,
                    "tracking_code": tracking_code,
                    "carrier_name": carrier_name,
                    "package_ids": package_ids,
                    "email_settings": email_settings,
                    "mailjet": mailjet,
                    "account_id": account_id,
                }

                _send_users(users, email_data)
