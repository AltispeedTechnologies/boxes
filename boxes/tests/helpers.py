"""Shared factories for Boxes unit tests."""
from decimal import Decimal

from django.contrib.auth.models import Group

from boxes.models import (
    Account, AccountBalance, Carrier, CustomUser, Package, PackageType, UserAccount,
)


def ensure_group(name):
    group, _ = Group.objects.get_or_create(name=name)
    return group


def make_user(username="tester", password="changem3", groups=None, **kwargs):
    user = CustomUser.objects.create_user(username=username, password=password, **kwargs)
    for g in groups or []:
        user.groups.add(ensure_group(g))
    return user


def make_account(user=None, name="Test Account", balance=Decimal("0.00"), billable=True, **kwargs):
    if user is None:
        user = make_user(username=f"owner_{Account.objects.count()}")
    account = Account.objects.create(
        user=user, name=name, balance=balance, billable=billable, **kwargs
    )
    AccountBalance.objects.get_or_create(
        account=account,
        defaults={"regular_balance": Decimal("0.00"), "late_balance": Decimal("0.00")},
    )
    return account


def link_user(user, account):
    return UserAccount.objects.get_or_create(user=user, account=account)[0]


def make_carrier(name="UPS"):
    return Carrier.objects.get_or_create(
        name=name, defaults={"phone_number": "555", "website": "https://example.com"}
    )[0]


def make_package_type(shortcode="B", description="Box", default_price=Decimal("6.00")):
    return PackageType.objects.get_or_create(
        shortcode=shortcode,
        defaults={"description": description, "default_price": default_price},
    )[0]


def make_package(account, carrier=None, package_type=None, tracking_code=None, **kwargs):
    carrier = carrier or make_carrier()
    package_type = package_type or make_package_type()
    if tracking_code is None:
        tracking_code = f"TRK{Package.objects.count():08d}"
    defaults = {
        "account": account,
        "carrier": carrier,
        "package_type": package_type,
        "tracking_code": tracking_code,
        "price": package_type.default_price,
        "current_state": 1,
        "paid": False,
    }
    defaults.update(kwargs)
    return Package.objects.create(**defaults)
