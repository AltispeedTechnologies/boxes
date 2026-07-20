"""Ensure demo billing accounts for fixture users after loaddata/reset."""
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from boxes.backend.account import create_billing_account, ensure_account_balance, ensure_customer_group
from boxes.backend.membership import associate_user
from boxes.backend.system import ensure_system_user
from boxes.models import Account, CustomUser, CustomUserEmail, UserAccount


class Command(BaseCommand):
    help = (
        "Ensure system user, Customer group membership, and a demo billing "
        "account for the fixture customer login (idempotent)."
    )

    def handle(self, *args, **options):
        ensure_system_user()
        Group.objects.get_or_create(name="Customer")
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Admin")
        Group.objects.get_or_create(name="Delivery")

        customer = CustomUser.objects.filter(username="customer").first()
        if customer is None:
            self.stdout.write("No customer fixture user; skipping demo account.")
            return

        ensure_customer_group(customer)
        if not CustomUserEmail.objects.filter(user=customer).exists() and customer.email:
            CustomUserEmail.objects.create(user=customer, email=customer.email)

        membership = UserAccount.objects.filter(user=customer, is_active=True).first()
        if membership:
            ensure_account_balance(membership.account)
            self.stdout.write(self.style.SUCCESS(
                f"Customer already linked to account {membership.account_id}."
            ))
            return

        actor = CustomUser.objects.filter(username="sysadmin").first() or ensure_system_user()
        account = create_billing_account(
            actor=actor,
            name=f"{customer.first_name} {customer.last_name}".strip() or "Demo Customer",
            billable=True,
            comments="Demo account created by bootstrap_demo",
            owner_user=customer,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Created demo account {account.id} for customer login."
        ))
