import os
import json
import random
import re
from boxes.models import *
from celery import shared_task
from collections import defaultdict
from datetime import timedelta
from django.db import transaction
from django.db.models import Count, F, Sum, Q
from django.utils import timezone
from faker import Faker
from mailjet_rest import Client

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

@shared_task
def age_picklists():
    today = timezone.now().date()
    future_date = today + timedelta(days=14)

    # Ensure Picklist entries exist for today through 14 days from now
    for single_date in (today + timedelta(n) for n in range((future_date - today).days + 1)):
        Picklist.objects.get_or_create(date=single_date)

    # Remove Picklist entries older than today with no corresponding PackagePicklist entries
    Picklist.objects.filter(date__lt=today, packagepicklist__isnull=True).delete()

    # Identify Picklist entries older than a week that have corresponding PackagePicklist entries
    week_old_date = today - timedelta(days=7)
    picklists_older_than_week_with_packages = Picklist.objects.filter(
        date__lt=week_old_date
    ).annotate(
        package_count=Count("packagepicklist")
    ).filter(package_count__gt=0).values_list("id", flat=True)

    # First, delete related PackagePicklist entries in bulk
    PackagePicklist.objects.filter(picklist_id__in=picklists_older_than_week_with_packages).delete()

    # Then, delete the Picklist entries
    Picklist.objects.filter(id__in=picklists_older_than_week_with_packages).delete()

@shared_task
def total_accounts(account_id=None):
    accounts_with_totals = Account.objects.annotate(
        total_credit=Sum("accountledger__credit"),
        total_debit=Sum("accountledger__debit")
    )

    if account_id is not None:
        accounts_with_totals = accounts_with_totals.filter(id=account_id)

    for account in accounts_with_totals:
        if account.total_credit or account.total_debit:
            new_balance = account.total_credit - account.total_debit
            # Only perform the update if the balance has changed
            if new_balance != account.balance:
                account.balance = new_balance
                account.save(update_fields=["balance"])

def get_frequency_delta(frequency):
    """Return a timedelta object based on the frequency."""
    if frequency == "D":
        return timedelta(days=1)
    elif frequency == "W":
        return timedelta(weeks=1)
    elif frequency == "M":
        return timedelta(days=365.2425) / 12
    return None

@shared_task
def age_charges():
    charge_rules = AccountChargeSettings.objects.filter(
        days__isnull=False,
        package_type_id__isnull=True, 
        price__isnull=True, 
        frequency__isnull=True,
        endpoint__isnull=True,
    ).order_by("days")

    custom_charge_rules = AccountChargeSettings.objects.filter(
        days__isnull=False,
        package_type_id__isnull=False, 
        price__isnull=False, 
        frequency__isnull=False,
        endpoint__isnull=True,
    ).order_by("days")

    endpoint_setting = AccountChargeSettings.objects.filter(
        endpoint__isnull=False
    ).values_list("endpoint", flat=True).first()

    #custom_package_types = [rule.package_type_id for rule in custom_charge_rules]
    #previous_days = None
    #for setting in charge_rules:
    #    start_time = timezone.now() - timedelta(days=setting.days)
    #    if not previous_days:
    #        assess_charges.delay(start_time, exclude_package_types=custom_package_types)
    #    else:
    #        end_time = timezone.now() - timedelta(days=previous_days)
    #        assess_charges.delay(start_time, end_time, exclude_package_types=custom_package_types)

    #    previous_days = setting.days

    custom_rules_by_type = defaultdict(list)
    for rule in custom_charge_rules:
        custom_rules_by_type[rule.package_type_id].append(rule)

    for package_type_id, rules in custom_rules_by_type.items():
        for rule in rules:
            frequency = get_frequency_delta(rule.frequency)
            initial_days = rule.days
            end_point_days = endpoint_setting if endpoint_setting else initial_days + 180

            start_time = timezone.now() - timedelta(days=initial_days)
            end_time = start_time + frequency
            price = rule.price if rule.price else None

            while (timezone.now() - end_time).days < end_point_days:
                assess_charges.delay(start_time, end_time, only_package_types=[package_type_id], price=price, offset=initial_days)
                end_time = start_time
                start_time -= frequency

@shared_task
def assess_charges(start_time, end_time=None, exclude_package_types=None, only_package_types=None, price=None, offset=None):
    start_time_adjusted = start_time + timedelta(days=offset) if offset else start_time
    end_time_adjusted = end_time + timedelta(days=offset) if offset and end_time else end_time

    # Define the base query for existing charges
    charges_query = AccountLedger.objects.filter(
        timestamp__gte=start_time_adjusted,
        package_id__isnull=False).select_related("package")
    
    if end_time:
        charges_query = charges_query.filter(timestamp__lt=end_time_adjusted)

    if exclude_package_types:
        charges_query = charges_query.exclude(package__package_type__in=exclude_package_types)
    elif only_package_types:
        charges_query = charges_query.filter(package__package_type__in=only_package_types)
    
    existing_charges = charges_query.values_list("package_id", flat=True)
    
    # Define the base query for checked-in packages
    checked_in_query = PackageLedger.objects.filter(timestamp__gte=start_time, state=1).select_related("package")
    
    if end_time:
        checked_in_query = checked_in_query.filter(timestamp__lt=end_time)

    if exclude_package_types:
        checked_in_query = checked_in_query.exclude(package__package_type__in=exclude_package_types)
    elif only_package_types:
        checked_in_query = checked_in_query.filter(package__package_type__in=only_package_types)
    
    checked_in_packages = checked_in_query.values_list("package_id", flat=True)

    # Find packages that are checked in but without an existing charge
    matching_ids = Q(id__in=checked_in_packages) & ~Q(id__in=existing_charges) & Q(current_state=1)

    # Prepare account ledger entries with a default debit value
    if price:
        packages_needing_charge = Package.objects.filter(matching_ids).values_list("id", "account_id")
        new_charges = (AccountLedger(user_id=1, package_id=pkg_id, account_id=acct_id, credit=0, debit=price) 
                       for pkg_id, acct_id in packages_needing_charge)
        package_ids = [data[0] for data in packages_needing_charge]
        packages_needing_charge.filter(id__in=package_ids).update(price=F("price") + price)
    else:
        packages_needing_charge = Package.objects.filter(matching_ids).values_list("id", "account_id", "price")
        new_charges = (AccountLedger(user_id=1, package_id=pkg_id, account_id=acct_id, credit=0, debit=price) 
                       for pkg_id, acct_id, price in packages_needing_charge)
    
    # Bulk create to optimize database operations
    AccountLedger.objects.bulk_create(new_charges)

@shared_task
def populate_seed_data():
    fake = Faker()

    # Generate unique names and tracking codes
    fake_names = set(fake.name() for _ in range(5000))
    fake_tracking_codes = set(fake.ean(length=13) for _ in range(20000))

    # Number of nascent Packages divided by number of nascent Accounts
    quotient, remainder = divmod(len(fake_tracking_codes), len(fake_names))

    # Create the new Accounts
    accounts = []
    for fake_name in fake_names:
        new_account = Account(user_id=1,
                              name=fake_name,
                              balance=0.00,
                              is_good_standing=True,
                              comments="")
        accounts.append(new_account)

    # Ensure that an (almost) equal amount of Packages match to each Account
    current_account, current_step = 1, 1
    packages = []
    for fake_tracking_code in fake_tracking_codes:
        new_package = Package(account_id=current_account,
                              carrier_id=random.randint(1, 4),
                              package_type_id=random.randint(1, 5),
                              inside=random.choice([True, False]),
                              tracking_code=fake_tracking_code,
                              current_state=1,
                              price=6.00,
                              comments="")
        packages.append(new_package)

        if current_step >= quotient:
            if current_step == quotient and remainder > 0:
                remainder -= 1
                current_step += 1
            else:
                current_step = 1
                current_account += 1
        else:
            current_step += 1

    Account.objects.bulk_create(accounts)
    Package.objects.bulk_create(packages)

    for account in accounts:
        account.ensure_primary_alias()

    # Identify packages without a corresponding state=1 ledger entry
    ledger_entries = PackageLedger.objects.filter(state=1).values_list("package_id", flat=True)
    missing_packages = Package.objects.exclude(id__in=ledger_entries).values_list("id", flat=True)

    # Create new ledger entries for these packages
    new_ledger_entries = (PackageLedger(user_id=1, package_id=package_id, state=1) for package_id in missing_packages)
    PackageLedger.objects.bulk_create(new_ledger_entries)

    # Start the other tasks
    age_picklists.delay()
    age_charges.delay()
