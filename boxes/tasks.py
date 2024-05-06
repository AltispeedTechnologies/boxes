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

@shared_task
def update_packages_background(ids, user_id, state, debit_credit_switch=False):
    Package.objects.filter(id__in=ids).update(current_state=state)
    account_ledger, package_ledger, affected_accounts = [], [], set()
    for pkg in Package.objects.filter(id__in=ids).values("id", "account_id", "price"):
        debit, credit = (0, pkg["price"]) if debit_credit_switch else (pkg["price"], 0)
        acct_entry = AccountLedger(user_id=user_id, package_id=pkg["id"],
                                   account_id=pkg["account_id"], debit=debit, credit=credit, description="")
        pkg_entry = PackageLedger(user_id=user_id, package_id=pkg["id"], state=state)
        account_ledger.append(acct_entry)
        package_ledger.append(pkg_entry)
        affected_accounts.add(pkg["account_id"])

    AccountLedger.objects.bulk_create(account_ledger)
    PackageLedger.objects.bulk_create(package_ledger)

    # Update balances for affected accounts
    accounts = Account.objects.filter(id__in=affected_accounts).annotate(
        total_credit=Sum("accountledger__credit", default=0),
        total_debit=Sum("accountledger__debit", default=0)
    )
    for account in accounts:
        new_balance = account.total_credit - account.total_debit
        if new_balance != account.balance:
            account.balance = new_balance
            account.save(update_fields=["balance"])
