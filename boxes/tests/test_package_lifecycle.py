"""Package check-in / check-out ledger behavior."""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.models import AccountLedger, Package, PackageLedger
from boxes.tests.helpers import link_user, make_account, make_package, make_user


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class PackageLifecycleTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.staff = make_user(username="staff1", groups=["Staff", "Customer"])
        self.account = make_account(user=self.staff, balance=Decimal("0.00"))
        self.package = make_package(self.account, price=Decimal("6.00"), current_state=1)
        self.client = Client()
        self.client.force_login(self.staff)

    @patch("boxes.views.packages.utility.total_accounts.delay")
    def test_checkout_then_reverse_does_not_double_debit(self, _delay):
        # Check out
        r1 = self.client.post("/packages/checkout/submit", {"ids[]": [self.package.id]})
        self.assertTrue(r1.json().get("success", r1.status_code == 200) or r1.status_code in (200, 302))
        self.package.refresh_from_db()
        debits_after_out = AccountLedger.objects.filter(package=self.package, debit__gt=0).count()

        # Reverse to checked-in
        r2 = self.client.post("/packages/checkout/reverse", {"ids[]": [self.package.id]})
        self.package.refresh_from_db()
        self.assertEqual(self.package.current_state, 1)
        debits_after_reverse = AccountLedger.objects.filter(package=self.package, debit__gt=0).count()
        self.assertEqual(
            debits_after_reverse,
            debits_after_out,
            "Re-check-in must not add another base package debit",
        )
