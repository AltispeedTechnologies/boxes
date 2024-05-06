from celery import shared_task
from django.db.models import Sum
from mailjet_rest import Client
from .models import *
import os
import json
import re

@shared_task
def send_email(account_id, package_id):
    api_key = os.environ["MJ_APIKEY_PUBLIC"]
    api_secret = os.environ["MJ_APIKEY_PRIVATE"]
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")

    email_settings = EmailSettings.objects.first()
    user_accounts = UserAccount.objects.filter(account__id=account_id)
    users = [user_account.user for user_account in user_accounts]

    tracking_code, carrier_name = Package.objects.filter(pk=package_id).values_list("tracking_code", "carrier__name").first()

    results = []

    for user in users:
        hr_name = user.first_name + " " + user.last_name
        email_content = email_settings.check_in_template.content

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
                    "Subject": email_settings.check_in_template.subject,
                    "TextPart": email_content,
                    "HTMLPart": email_content
                }
            ]
        }

        result = mailjet.send.create(data=email_payload)
        results.append(result.json())

    return results
