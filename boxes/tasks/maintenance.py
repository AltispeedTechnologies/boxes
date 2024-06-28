import random
from boxes.backend import reports as reports_backend
from boxes.backend.account import create_user_from_account
from boxes.models import (Account, Chart, Package, PackageLedger, PackagePicklist, PackageQueue, Picklist,
                          PicklistQueue, Queue)
from boxes.models.chart import CHART_FREQUENCIES
from boxes.tasks.charges import age_charges
from celery import shared_task
from datetime import timedelta
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.utils import timezone
from faker import Faker


@shared_task
def age_picklists():
    today = timezone.now().date()
    future_date = today + timedelta(days=14)

    with transaction.atomic():
        # Ensure Picklist entries exist for today through 14 days from now
        for single_date in (today + timedelta(n) for n in range((future_date - today).days + 1)):
            try:
                Picklist.objects.get_or_create(date=single_date)
            # Multiple entries are fine, ignore the exception
            except MultipleObjectsReturned:
                continue

        # Remove empty picklists with no queue
        Picklist.objects.filter(date__lt=today, packagepicklist__isnull=True, picklistqueue__isnull=True).delete()

        # Identify Picklist entries older than a week that have corresponding PackagePicklist entries
        week_old_date = today - timedelta(days=7)
        picklists_to_remove = Picklist.objects.filter(
            date__lt=week_old_date
        ).values_list("id", flat=True)

        # Some picklists still have implicit PackageQueue entries; exclude those from the final deletion
        except_these_picklists = []

        # Delete related PackagePicklist and PackageQueue entries
        package_picklists = PackagePicklist.objects.filter(picklist_id__in=picklists_to_remove)
        for package_picklist in package_picklists:
            picklist_id = package_picklist.picklist_id
            if picklist_id not in except_these_picklists:
                except_these_picklists.append(picklist_id)

        picklist_queues = PicklistQueue.objects.filter(picklist_id__in=picklists_to_remove)
        for picklist_queue in picklist_queues:
            package_queue = PackageQueue.objects.filter(queue_id=picklist_queue.queue_id)
            if package_queue.count() > 0:
                picklist_id = picklist_queue.picklist_id
                if picklist_id not in except_these_picklists:
                    except_these_picklists.append(picklist_queue.picklist_id)
            else:
                package_queue.delete()
                picklist_queue.delete()
                Queue.objects.filter(pk=picklist_queue.queue_id).delete()

        # Filter out the Picklists with queue entries
        picklists_to_remove = [i for i in picklists_to_remove if i not in except_these_picklists]

        # Delete the Picklist entries
        Picklist.objects.filter(id__in=picklists_to_remove).delete()


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
                              billable=True,
                              comments="")
        accounts.append(new_account)

    # Ensure that an (almost) equal amount of Packages match to each Account
    current_account, current_step = 1, 1
    packages = []
    for fake_tracking_code in fake_tracking_codes:
        new_package = Package(account_id=current_account,
                              carrier_id=random.randint(1, 4),
                              package_type_id=random.randint(1, 3),
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
        create_user_from_account(account_id)

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


@shared_task
def regenerate_report_data():
    with transaction.atomic():
        for freq, _ in CHART_FREQUENCIES:
            # Grab the chart data
            chart_data, total_data = reports_backend.report_chart_generate(freq)

            chart, created = Chart.objects.update_or_create(
                frequency=freq,
                defaults={
                    "total_data": total_data,
                    "chart_data": chart_data,
                    "last_updated": timezone.now()
                }
            )
