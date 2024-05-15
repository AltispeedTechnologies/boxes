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
from django.utils.crypto import get_random_string
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

@shared_task
def create_user_from_account(account_id):
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return None, None

    # If no UserAccount entry exists, create a CustomUser
    # Split the account.name into name parts
    name_parts = account.name.split(" ")

    # If the account name is empty, do nothing
    if len(name_parts) == 0:
        return None, account

    first_name, middle_name, last_name = name_parts[0], "", ""

    if len(name_parts) >= 3:
        middle_name = name_parts[1]
        last_name = " ".join(name_parts[2:])
    elif len(name_parts) == 2:
        middle_name = ""
        last_name = name_parts[1]

    # Create a CustomUser with a useless password and login disabled
    new_custom_user = CustomUser.objects.create(
        username=account.name[:150],
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        is_active=False,
        password=get_random_string(128),
        date_joined=timezone.now()
    )
    # Create a UserAccount with the new CustomUser
    UserAccount.objects.create(user=new_custom_user, account=account)
    # Return the new CustomUser object
    return new_custom_user.id

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

    custom_package_types = [rule.package_type_id for rule in custom_charge_rules]
    previous_days = None
    for setting in charge_rules:
        start_time = timezone.now() - timedelta(days=setting.days)
        if not previous_days:
            assess_regular_charges.delay(start_time.timestamp())
        else:
            end_time = timezone.now() - timedelta(days=previous_days)
            assess_regular_charges.delay(start_time.timestamp(), end_time.timestamp(), custom_package_types)
        previous_days = setting.days

    custom_rules_by_type = defaultdict(list)
    for rule in custom_charge_rules:
        custom_rules_by_type[rule.package_type_id].append(rule)

    for package_type_id, rules in custom_rules_by_type.items():
        for rule in rules:
            frequency_seconds = get_frequency_delta(rule.frequency).total_seconds()
            initial_days = rule.days
            price = rule.price if rule.price else None
            endpoint_days = endpoint_setting if endpoint_setting else initial_days + 180

            check_in_date = timezone.now() - timedelta(days=initial_days)
            endpoint_date = timezone.now() - timedelta(days=endpoint_days)

            assess_custom_charges.delay(endpoint_date.timestamp(), check_in_date.timestamp(), package_type_id, frequency_seconds, initial_days, price)

@shared_task
def assess_regular_charges(start_time, end_time=None, exclude_package_types=None):
    start_time = timezone.datetime.fromtimestamp(start_time)
    end_time = timezone.datetime.fromtimestamp(end_time) if end_time else None

    charges_query = AccountLedger.objects.filter(
        timestamp__gte=start_time,
        package_id__isnull=False
    ).select_related("package")

    if end_time:
        charges_query = charges_query.filter(timestamp__lt=end_time)

    if exclude_package_types:
        charges_query = charges_query.exclude(package__package_type__in=exclude_package_types)

    existing_charges = charges_query.values_list("package_id", flat=True)

    checked_in_query = PackageLedger.objects.filter(
        timestamp__gte=start_time, state=1
    ).select_related("package")

    if end_time:
        checked_in_query = checked_in_query.filter(timestamp__lt=end_time)

    if exclude_package_types:
        checked_in_query = checked_in_query.exclude(package__package_type__in=exclude_package_types)

    checked_in_packages = checked_in_query.values_list("package_id", flat=True)

    matching_ids = Q(id__in=checked_in_packages) & ~Q(id__in=existing_charges) & Q(current_state=1)
    matching_packages = Package.objects.filter(matching_ids)

    packages_needing_charge = Package.objects.filter(matching_ids).values_list("id", "account_id", "price")
    new_charges = (AccountLedger(
        user_id=1, package_id=pkg_id, account_id=acct_id, credit=0, debit=price
    ) for pkg_id, acct_id, price in packages_needing_charge)

    AccountLedger.objects.bulk_create(new_charges)
    total_accounts.delay()

@shared_task
def assess_custom_charges(endpoint_date, check_in_date, package_type_id, frequency_seconds, initial_days, price):
    endpoint_date = timezone.make_aware(timezone.datetime.fromtimestamp(endpoint_date))
    check_in_date = timezone.make_aware(timezone.datetime.fromtimestamp(check_in_date))
    frequency = timedelta(seconds=frequency_seconds)

    # Retrieve the checked-in packages once
    checked_in_query = PackageLedger.objects.filter(
        timestamp__lte=timezone.now(), state=1, package__package_type=package_type_id
    ).select_related("package")

    checked_in_packages = checked_in_query.values_list("package_id", "package__account_id", "timestamp")

    new_charges = []
    account_ids = set()
    price_increments = defaultdict(int)
    for package_id, account_id, check_in_timestamp in checked_in_packages:
        # Calculate the start time as check-in time + initial_days offset
        current_time = check_in_timestamp + timedelta(days=initial_days)

        while current_time <= timezone.now():
            charge_exists = AccountLedger.objects.filter(
                package_id=package_id, timestamp=current_time
            ).exists()
            if not charge_exists:
                new_charges.append(AccountLedger(
                    user_id=1, package_id=package_id, account_id=account_id,
                    credit=0, debit=price, timestamp=current_time
                ))
                account_ids.add(account_id)
                price_increments[package_id] += price
            current_time += frequency

    if new_charges:
        AccountLedger.objects.bulk_create(new_charges)
        for account_id in account_ids:
            total_accounts.delay(account_id=account_id)
        for package_id, increment in price_increments.items():
            Package.objects.filter(id=package_id).update(price=F("price") + increment)

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
    account_ids = set()
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
        account_ids.add(current_account)

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

    for account_id in account_ids:
        create_user_from_account.delay(account_id)

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
