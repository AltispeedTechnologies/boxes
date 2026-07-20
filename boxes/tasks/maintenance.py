"""Picklist aging, seed data, and report refresh tasks."""
import random
from datetime import timedelta

from celery import shared_task
from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from django.utils import timezone
from faker import Faker

from boxes.backend import reports as reports_backend
from boxes.backend.account import create_user_from_account
from boxes.backend.system import get_system_user
from boxes.models import (
    Account,
    Chart,
    Package,
    PackageLedger,
    PackagePicklist,
    PackageQueue,
    Picklist,
    PicklistQueue,
    Queue,
)
from boxes.models.chart import CHART_FREQUENCIES
from boxes.tasks.charges import age_charges


@shared_task
def age_picklists():
    """Celery beat: age or clean up old picklists."""
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
def populate_seed_data(account_count=5000, package_count=20000, run_followups=True):
    """Create demo accounts/packages for development.

    ``account_count`` / ``package_count`` can be reduced for lightweight seeds.
    Packages are attached to the newly created accounts (not hardcoded pk=1).
    When ``run_followups`` is True, enqueue age_picklists / age_charges.
    """
    fake = Faker()
    account_count = max(1, int(account_count or 5000))
    package_count = max(1, int(package_count or 20000))

    # Generate unique names and tracking codes
    fake_names = set()
    while len(fake_names) < account_count:
        fake_names.add(fake.name())
    fake_tracking_codes = set()
    while len(fake_tracking_codes) < package_count:
        fake_tracking_codes.add(fake.ean(length=13))

    system_pk = get_system_user().pk
    accounts = [
        Account(
            user_id=system_pk,
            name=fake_name,
            balance=0.00,
            billable=True,
            comments="",
        )
        for fake_name in fake_names
    ]
    Account.objects.bulk_create(accounts)
    # Refresh with real primary keys
    created_accounts = list(
        Account.objects.filter(name__in=list(fake_names)).order_by("id")
    )
    if not created_accounts:
        return

    account_ids = [a.id for a in created_accounts]
    n_accounts = len(account_ids)
    quotient, remainder = divmod(len(fake_tracking_codes), n_accounts)

    packages = []
    account_index = 0
    current_step = 1
    # Max packages for current account slot
    limit = quotient + (1 if remainder > 0 else 0)
    if remainder > 0:
        remainder -= 1

    for fake_tracking_code in fake_tracking_codes:
        packages.append(Package(
            account_id=account_ids[account_index],
            carrier_id=random.randint(1, 4),
            package_type_id=random.randint(1, 3),
            inside=random.choice([True, False]),
            tracking_code=fake_tracking_code,
            current_state=1,
            price=6.00,
            comments="",
        ))
        if current_step >= limit:
            current_step = 1
            account_index = min(account_index + 1, n_accounts - 1)
            limit = quotient + (1 if remainder > 0 else 0)
            if remainder > 0:
                remainder -= 1
        else:
            current_step += 1

    Package.objects.bulk_create(packages)

    for account_id in account_ids:
        create_user_from_account(account_id)

    for account in created_accounts:
        account.ensure_primary_alias()

    # Identify packages without a corresponding state=1 ledger entry
    ledger_entries = PackageLedger.objects.filter(state=1).values_list("package_id", flat=True)
    missing_packages = Package.objects.exclude(id__in=ledger_entries).values_list("id", flat=True)

    new_ledger_entries = (
        PackageLedger(user_id=system_pk, package_id=package_id, state=1)
        for package_id in missing_packages
    )
    PackageLedger.objects.bulk_create(new_ledger_entries)

    if run_followups:
        age_picklists.delay()
        age_charges.delay()


@shared_task
def regenerate_report_data():
    """Celery beat: refresh chart/report cached data."""
    with transaction.atomic():
        for freq, _ in CHART_FREQUENCIES:
            # Grab the chart data
            chart_data, total_data = reports_backend.report_chart_generate(freq)

            Chart.objects.update_or_create(
                frequency=freq,
                defaults={
                    "total_data": total_data,
                    "chart_data": chart_data,
                    "last_updated": timezone.now(),
                },
            )
