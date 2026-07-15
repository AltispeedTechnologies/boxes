"""Tests for account balance helpers."""
from decimal import Decimal

from django.test import TestCase, override_settings

from boxes.tests.helpers import make_account, make_user


@override_settings(ALLOWED_HOSTS=["*"])
class BalanceHelperTests(TestCase):
    def test_amount_owed_from_negative_balance(self):
        user = make_user()
        account = make_account(user=user, balance=Decimal("-12.50"))
        self.assertEqual(account.amount_owed(), Decimal("12.50"))
        self.assertEqual(account.hr_balance(), "$12.50")

    def test_amount_owed_zero_when_credit(self):
        user = make_user(username="credit")
        account = make_account(user=user, balance=Decimal("5.00"))
        self.assertEqual(account.amount_owed(), Decimal("0.00"))
        self.assertEqual(account.display_balance_amount(), Decimal("5.00"))
