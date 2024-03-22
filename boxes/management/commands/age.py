from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q, Sum
from django.utils import timezone
from boxes.models import Package, PackageLedger, Account, AccountLedger

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Creating missing records"))

        # If a package is checked in but does not have an appropriate ledger
        # entry, create it
        self.create_missing_ledger_entries()

        self.stdout.write(self.style.NOTICE("Assessing the charges"))

        # Create the initial charge if one does not already exist
        # This is a precautionary measure
        self.assess_charges(timezone.now() - timedelta(days=90), "initial")

        # Create the second charge iff the item is between 90 and 180 days
        self.assess_charges(timezone.now() - timedelta(days=180), "second", timezone.now() - timedelta(days=90))

        self.stdout.write(self.style.NOTICE("Total the account balances"))

        # Update the balance for every account given the ledger
        self.total_accounts()

        self.stdout.write(self.style.SUCCESS("Aging completed successfully"))

    def create_missing_ledger_entries(self):
        # Identify packages without a corresponding state=1 ledger entry
        ledger_entries = PackageLedger.objects.filter(state=1).values_list("package_id", flat=True)
        missing_packages = Package.objects.exclude(id__in=ledger_entries).values_list("id", flat=True)

        # Prepare new ledger entries for these packages
        new_ledger_entries = (PackageLedger(user_id=1, package_id=package_id, state=1) for package_id in missing_packages)
        
        # Bulk create to optimize database operations
        PackageLedger.objects.bulk_create(new_ledger_entries)

    def assess_charges(self, start_time, charge_type, end_time=None):
        # Define the base query for existing charges
        charges_query = AccountLedger.objects.filter(timestamp__gte=start_time, package_id__isnull=False)
        
        if end_time:
            charges_query = charges_query.filter(timestamp__lt=end_time)
        
        existing_charges = charges_query.values_list("package_id", flat=True)
        
        # Define the base query for checked-in packages
        checked_in_query = PackageLedger.objects.filter(timestamp__gte=start_time, state=1)
        
        if end_time:
            checked_in_query = checked_in_query.filter(timestamp__lt=end_time)
        
        checked_in_packages = checked_in_query.values_list("package_id", flat=True)

        # Find packages that are checked in but without an existing charge
        matching_ids = Q(id__in=checked_in_packages) & ~Q(id__in=existing_charges) & Q(current_state=1)
        packages_needing_charge = Package.objects.filter(matching_ids).values_list("id", "account_id", "price")

        # Prepare account ledger entries with a default debit value
        new_charges = (AccountLedger(user_id=1, package_id=pkg_id, account_id=acct_id, credit=0, debit=price) 
                       for pkg_id, acct_id, price in packages_needing_charge)
        
        # Bulk create to optimize database operations
        AccountLedger.objects.bulk_create(new_charges)

    def total_accounts(self):
        accounts_with_totals = Account.objects.annotate(
            total_credit=Sum("accountledger__credit"),
            total_debit=Sum("accountledger__debit")
        )

        for account in accounts_with_totals:
            # Ensure both of these values are not null
            if account.total_credit or account.total_debit:
                new_balance = account.total_credit - account.total_debit
                # Only perform the update if the balance has changed
                if new_balance != account.balance:
                    account.balance = new_balance
                    account.save(update_fields=["balance"])
