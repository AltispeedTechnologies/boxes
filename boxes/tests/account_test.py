from django.test import TestCase
from boxes.models import *


class AccountTest(TestCase):
    def setUp(self):
        self.user = CustomUser()
        self.user.save()

    def test_create_account(self):
        # Create an Account instance
        account = Account.objects.create(
            user=self.user,
            balance=100.00,
            is_good_standing=True,
            description="Sample account"
        )

        # Retrieve the created account from the database
        retrieved_account = Account.objects.get(pk=account.pk)

        # Check if the retrieved account matches the created one
        self.assertEqual(retrieved_account.user, self.user)
        self.assertEqual(retrieved_account.balance, 100.00)
        self.assertEqual(retrieved_account.is_good_standing, True)
        self.assertEqual(retrieved_account.description, "Sample account")

    def test_create_account_ledger(self):
        # Create an Account instance
        account = Account.objects.create(
            user=self.user,
            balance=100.00,
            is_good_standing=True,
            description="Sample account"
        )

        # Create an AccountLedger instance
        ledger_entry = AccountLedger.objects.create(
            account=account,
            credit=50.00,
            debit=0.00,
            description="Credit entry"
        )

        # Retrieve the created ledger entry from the database
        retrieved_entry = AccountLedger.objects.get(pk=ledger_entry.pk)

        # Check if the retrieved ledger entry matches the created one
        self.assertEqual(retrieved_entry.account, account)
        self.assertEqual(retrieved_entry.credit, 50.00)
        self.assertEqual(retrieved_entry.debit, 0.00)
        self.assertEqual(retrieved_entry.description, "Credit entry")

    def test_create_user_account(self):
        account = Account.objects.create(
            user=self.user,
            balance=100.00,
            is_good_standing=True,
            description="Sample account"
        )
        user_account = UserAccount.objects.create(
            user=self.user,
            account=account
        )

        # Check if the retrieved user account matches the created one
        self.assertEqual(user_account.user, self.user)
        self.assertEqual(user_account.account, account)

    def test_account_ledger_relationship(self):
        # Create an Account instance
        account = Account.objects.create(
            user=self.user,
            balance=100.00,
            is_good_standing=True,
            description="Sample account"
        )

        # Create an AccountLedger instance
        ledger_entry = AccountLedger.objects.create(
            account=account,
            credit=50.00,
            debit=0.00,
            description="Credit entry"
        )

        # Retrieve the account from the ledger entry relationship
        ledger_account = ledger_entry.account

        # Check if the retrieved account matches the created one
        self.assertEqual(ledger_account, account)

    def test_user_account_relationships(self):
        # Create an Account instance
        account = Account.objects.create(
            user=self.user,
            balance=100.00,
            is_good_standing=True,
            description="Sample account"
        )

        # Create a UserAccount instance
        user_account = UserAccount.objects.create(
            user=self.user,
            account=account
        )

        # Retrieve the account from the user account relationship
        user_account_account = user_account.account

        # Check if the retrieved account matches the created one
        self.assertEqual(user_account_account, account)
