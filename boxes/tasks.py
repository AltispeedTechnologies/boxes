from celery import shared_task
from django.db import transaction
from django.db.models import Sum
from mailjet_rest import Client
from .models import *
import os
import json
import re

@shared_task
def send_emails():
    api_key = os.environ["MJ_APIKEY_PUBLIC"]
    api_secret = os.environ["MJ_APIKEY_PRIVATE"]
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")

    email_settings = EmailSettings.objects.first()

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

            for user in users:
                hr_name = user.first_name + " " + user.last_name
                email_content = template.content

                pattern = r'<span [^>]*class="custom-block[^"]*"[^>]*>([^<]+)</span>'
                email_content = re.sub(pattern, lambda m: f'{{{m.group(1).lower().replace(" ", "_")}}}', email_content)
                email_content = email_content.format(first_name=user.first_name,
                                                     last_name=user.last_name,
                                                     tracking_code=tracking_code,
                                                     carrier=carrier_name)

                email_payload = {
                    "Messages": [
                        {
                            "From": {
                                "Email": email_settings.sender_email,
                                "Name": email_settings.sender_name
                            },
                            "To": [
                                {
                                    "Email": email_settings.sender_email,
                                    "Name": hr_name
                                }
                            ],
                            "Subject": template.subject,
                            "TextPart": email_content,
                            "HTMLPart": email_content
                        }
                    ]
                }

                result = mailjet.send.create(data=email_payload)
