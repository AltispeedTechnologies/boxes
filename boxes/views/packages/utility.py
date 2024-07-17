from boxes.management.exception_catcher import exception_catcher
from boxes.models import (Account, AccountLedger, Carrier, Package, PackageLedger, PackagePicklist, PackageQueue,
                          PackageType, UserAccount)
from boxes.tasks import total_accounts
from collections import defaultdict
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse


@exception_catcher()
def update_packages_fields(package_ids, package_data, user, no_ledger=False):
    packages = Package.objects.filter(pk__in=package_ids)
    updates = []
    errors = []

    fields_to_update = {
        "tracking_code": str,
        "price": Decimal,
        "comments": str,
        "account_id": int,
        "carrier_id": int,
        "package_type_id": int,
        "inside": bool
    }

    accounts = {}
    account_ledger = []

    for package in packages:
        for field, type_func in fields_to_update.items():
            if field not in package_data or package_data[field] is None:
                continue

            field_data = package_data[field]
            if type_func != bool:
                field_data = field_data.strip()

            if field == "account_id":
                entity = Account.objects.get(id=field_data)
                if package.account_id != entity.id:
                    with transaction.atomic():
                        # Bulk update AccountLedger objects
                        AccountLedger.objects.filter(account_id=package.account_id).update(account_id=entity.id)

                        # Store old and new user mappings, update PackageLedger accordingly
                        old_users = UserAccount.objects.filter(
                            account_id=package.account_id
                        ).values_list(
                            "user_id", flat=True
                        )

                        new_user = UserAccount.objects.filter(
                            account_id=entity.id
                        ).values_list(
                            "user_id", flat=True
                        ).first()

                        PackageLedger.objects.filter(user_id__in=old_users).update(user_id=new_user)

                    package.account = entity
            elif field == "carrier_id":
                entity = Carrier.objects.get(id=field_data)
                package.carrier = entity
            elif field == "package_type_id":
                entity = PackageType.objects.get(id=field_data)
                package.package_type = entity
            elif field == "comments" and package_data[field] is None:
                package.comments = ""
            elif field == "price":
                field_data = type_func(field_data)
                if package.price != field_data:
                    change_in_price = package.price - field_data
                    credit = max(change_in_price, 0)
                    debit = -min(change_in_price, 0)

                    account_id = package.account_id
                    if account_id in accounts:
                        accounts[account_id].balance += change_in_price
                    else:
                        current_balance = Account.objects.filter(
                            pk=account_id
                        ).values_list(
                            "balance", flat=True
                        ).first()

                        if current_balance is not None:
                            new_balance = current_balance + change_in_price
                            accounts[account_id] = Account(id=account_id, balance=new_balance)

                    if not no_ledger:
                        account_ledger.append(AccountLedger(
                            user_id=user.id, package_id=package.id,
                            account_id=account_id, debit=debit,
                            credit=credit, description="Price changed", is_late=False
                        ))

                    package.price = field_data
            else:
                setattr(package, field, type_func(field_data))

        updates.append(package)

    with transaction.atomic():
        if updates:
            Package.objects.bulk_update(updates, fields_to_update.keys())

        if accounts:
            Account.objects.bulk_update(accounts.values(), ["balance"])

        if account_ledger:
            AccountLedger.objects.bulk_create(account_ledger)

    if errors:
        return JsonResponse({"success": False, "errors": errors})


def update_packages_util(request, state, debit_credit_switch=False):
    response_data = {"success": False, "errors": []}
    try:
        ids = request.POST.getlist("ids[]", [])
        if not ids:
            raise ValueError("No package IDs provided.")

        # Update the state
        Package.objects.filter(id__in=ids).update(current_state=state)

        # If an Account is not billable, mark all its packages as paid
        Package.objects.filter(id__in=ids, account__billable=False, paid=False).update(paid=True)

        # If there is a positive account balance that covers the price of a given Package, mark it as paid
        account_packages = defaultdict(lambda: {"balance": 0, "packages": []})
        for package in Package.objects.filter(
                id__in=ids, account__billable=True, paid=False, account__balance__gt=0
                ).values("id", "price", "account_id", "account__balance").order_by("id"):
            account_id = package["account_id"]
            account_packages[account_id]["balance"] = package["account__balance"]
            account_packages[account_id]["packages"].append((package["id"], package["price"]))
        mark_paid = []
        for _, data in account_packages.items():
            running_balance = data["balance"]
            for pkg_id, price in data["packages"]:
                if running_balance <= 0:
                    break
                elif price > running_balance:
                    continue
                elif price <= running_balance:
                    running_balance -= price
                    mark_paid.append(pkg_id)
        if len(mark_paid) > 0:
            Package.objects.filter(id__in=mark_paid).update(paid=True)

        # Remove the packages from all queues and picklists in the process
        PackageQueue.objects.filter(package_id__in=ids).delete()
        PackagePicklist.objects.filter(package_id__in=ids).delete()

        account_ledger, package_ledger, affected_accounts = [], [], set()
        for pkg in Package.objects.filter(id__in=ids).values("id", "account_id", "price"):
            pkg_entry = PackageLedger(user_id=request.user.id, package_id=pkg["id"], state=state)
            package_ledger.append(pkg_entry)

            if pkg["price"] == 0:
                continue

            debit, credit = (0, pkg["price"]) if debit_credit_switch else (pkg["price"], 0)
            acct_entry = AccountLedger(user_id=request.user.id, package_id=pkg["id"], is_late=False,
                                       account_id=pkg["account_id"], debit=debit, credit=credit, description="")
            account_ledger.append(acct_entry)
            affected_accounts.add(pkg["account_id"])

        AccountLedger.objects.bulk_create(account_ledger)
        PackageLedger.objects.bulk_create(package_ledger)

        # Update balances for affected accounts
        for account_id in affected_accounts:
            total_accounts.delay(account_id=account_id)

        response_data["success"] = True
        return response_data
    except ValidationError as e:
        response_data["errors"] = [str(message) for message in e.messages]
    except Exception as e:
        response_data["errors"] = [str(e)]
    return response_data
