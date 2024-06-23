from boxes.models import Account, AccountBalance, AccountChargeSettings, AccountLedger, Package, PackageLedger
from celery import shared_task
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone


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
            assess_regular_charges.delay(start_time.timestamp(), end_time.timestamp(), custom_package_types,
                                         setting.days)
        previous_days = setting.days

    if endpoint_setting and (not previous_days or endpoint_setting > previous_days):
        start_time = timezone.now() - timedelta(days=endpoint_setting)
        if previous_days:
            end_time = timezone.now() - timedelta(days=previous_days)
            assess_regular_charges.delay(start_time.timestamp(), end_time.timestamp(), custom_package_types,
                                         previous_days)
        else:
            assess_regular_charges.delay(start_time.timestamp())

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

            assess_custom_charges.delay(endpoint_date.timestamp(), check_in_date.timestamp(), package_type_id,
                                        frequency_seconds, initial_days, price)


@shared_task
def assess_regular_charges(start_time, end_time=None, exclude_package_types=None, rule_days=None):
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

    checked_in_packages_ids = checked_in_query.values_list("package_id", flat=True)

    matching_ids = Q(id__in=checked_in_packages_ids) & ~Q(id__in=existing_charges) & Q(current_state=1) & ~Q(price=0.00)
    packages_needing_charge = Package.objects.filter(matching_ids).values_list("id", "account_id", "price")
    checked_in_packages = checked_in_query.values_list("package_id", "timestamp")

    new_charges = []
    for pkg_id, acct_id, price in packages_needing_charge:
        check_in_timestamp = dict(checked_in_packages).get(pkg_id)
        if check_in_timestamp:
            charge_time = check_in_timestamp + timedelta(days=rule_days) if rule_days else check_in_timestamp
            is_late = check_in_timestamp != charge_time
            description = "Late charge" if is_late else "Parcel charge"
            new_charges.append(AccountLedger(
                user_id=1, package_id=pkg_id, account_id=acct_id, credit=0,
                debit=price, timestamp=charge_time, is_late=is_late, description=description
            ))

    # Bulk create new charges if any
    if new_charges:
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
                    credit=0, debit=price, timestamp=current_time, is_late=True
                ))
                account_ids.add(account_id)
            current_time += frequency

    if new_charges:
        AccountLedger.objects.bulk_create(new_charges)
        for account_id in account_ids:
            total_accounts.delay(account_id=account_id)


@shared_task
def total_accounts(account_id=None):
    if account_id is not None:
        accounts = Account.objects.filter(id=account_id)
    else:
        accounts = Account.objects.all()

    accounts_with_totals = accounts.annotate(
        total_regular_credit=Coalesce(Sum("accountledger__credit",
                                      filter=Q(accountledger__is_late=False)),
                                      Decimal("0.00")),
        total_regular_debit=Coalesce(Sum("accountledger__debit",
                                     filter=Q(accountledger__is_late=False)),
                                     Decimal("0.00")),
        total_late_credit=Coalesce(Sum("accountledger__credit",
                                   filter=Q(accountledger__is_late=True)),
                                   Decimal("0.00")),
        total_late_debit=Coalesce(Sum("accountledger__debit",
                                  filter=Q(accountledger__is_late=True)),
                                  Decimal("0.00"))
    )

    for account in accounts_with_totals:
        new_regular_balance = account.total_regular_credit - account.total_regular_debit
        new_late_balance = account.total_late_credit - account.total_late_debit

        with transaction.atomic():
            account_balance, created = AccountBalance.objects.get_or_create(
                account=account,
                defaults={"regular_balance": new_regular_balance, "late_balance": new_late_balance}
            )

            if (new_regular_balance != account_balance.regular_balance or
                    new_late_balance != account_balance.late_balance):
                account_balance.regular_balance = new_regular_balance
                account_balance.late_balance = new_late_balance
                account_balance.save()

            account.balance = new_regular_balance + new_late_balance
            account.save()
