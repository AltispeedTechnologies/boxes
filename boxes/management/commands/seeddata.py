from boxes.models import *
from django.core.management.base import BaseCommand
from faker import Faker
import random

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        fake = Faker()

        # Generate unique names and tracking codes
        fake_names = set(fake.name() for _ in range(5000))
        fake_tracking_codes = set(fake.ean(length=13) for _ in range(20000))

        # Number of nascent Packages divided by number of nascent Accounts
        quotient, remainder = divmod(len(fake_tracking_codes), len(fake_names))

        # Create the new Accounts
        accounts = []
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

        for account in accounts:
            account.ensure_primary_alias()
