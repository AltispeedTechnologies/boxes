import os
import json
import re
from boxes.models import (CustomUserEmail, EmailQueue, EmailSettings, GlobalSettings, Package, SentEmail,
                          SentEmailContents, SentEmailPackage, SentEmailResult, UserAccount)
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


def _send_email(email_html, email_settings, email_text, hr_name, mailjet, package_ids, recipient_email, template,
                account_id):
    email_payload = {
        "Messages": [
            {
                "From": {
                        "Email": email_settings.sender_email,
                        "Name": email_settings.sender_name
                },
                "To": [
                    {
                        "Email": recipient_email,
                        "Name": hr_name
                    }
                ],
                "Subject": template.subject,
                "TextPart": email_text,
                "HTMLPart": email_html
            }
        ]
    }

    # Send the email
    result = mailjet.send.create(data=email_payload)

    # Interpret the immediate result and store it for later analyzation
    json_result = result.json()
    json_message = json_result["Messages"][0]
    success = False
    # See https://dev.mailjet.com/email/guides/send-api-v31/
    if json_message["Status"] == "success":
        success = True

    # We are only sending one email per request, so it will always be the first item
    # If there is no message_uuid from the response, we can assume it was also unsuccessful
    message_uuid = None
    if success:
        message_uuid = json_message["To"][0]["MessageUUID"]

    # Create main SentEmail object
    sent_email = SentEmail.objects.create(account_id=account_id,
                                          subject=template.subject,
                                          email=recipient_email,
                                          success=success,
                                          message_uuid=message_uuid)
    # Store the contents of the sent email
    SentEmailContents.objects.create(sent_email=sent_email, html=email_html)
    # Ensure each package can have a record of a sent email
    for package_id in package_ids:
        SentEmailPackage.objects.create(sent_email=sent_email, package_id=package_id)
    # Store the raw JSON result, in case something goes haywire
    SentEmailResult.objects.create(sent_email=sent_email, response=json_result)


def _send_users(users, template, tracking_code, carrier_name, package_ids, email_settings, mailjet, account_id):
    for user in users:
        hr_name = user.first_name + " " + user.last_name
        email_html = template.content

        pattern = r'<span [^>]*class="custom-block[^"]*"[^>]*>([^<]+)</span>'
        email_html = re.sub(pattern, lambda m: f'{{{m.group(1).lower().replace(" ", "_")}}}', email_html)
        email_html = email_html.format(first_name=user.first_name,
                                       last_name=user.last_name,
                                       tracking_code=tracking_code,
                                       carrier=carrier_name)

        # Remove all HTML tags
        email_text = re.sub(r"<[^>]+>", "", email_html)
        # Replace <br> and <br/> with newlines
        email_text = re.sub(r"<br\s*/?>", "\n", email_text, flags=re.IGNORECASE)
        email_text = unescape(email_text)

        for recipient_email_obj in CustomUserEmail.objects.filter(user=user):
            recipient_email = recipient_email_obj.email
            _send_email(email_html, email_settings, email_text, hr_name, mailjet, package_ids, recipient_email,
                        template, account_id)


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

            if len(results) > 1:
                # Create comma-separated lists if multiple results
                tracking_code = ", ".join([result[0] for result in results])
                unique_carrier_names = set(result[1] for result in results)
                carrier_name = ", ".join(unique_carrier_names)
            elif results:
                # Direct assignment if only one result
                tracking_code, carrier_name = results[0]
            else:
                continue

            _send_users(users, template, tracking_code, carrier_name, package_ids, email_settings, mailjet, account_id)
