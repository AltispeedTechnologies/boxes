from boxes.management.exception_catcher import exception_catcher
from boxes.models import (Account, AccountLedger, Carrier, Package, PackageLedger, PackagePicklist, PackageQueue,
                          PackageType)
from boxes.tasks import total_accounts
from decimal import Decimal
from django.core.exceptions import ValidationError
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

    accounts, account_ledger = {}, []

    for package in packages:
        for field, type_func in fields_to_update.items():
            if field not in package_data.keys():
                continue
            elif package_data[field] is None:
                continue

            if type_func == bool:
                field_data = package_data[field]
            else:
                field_data = package_data[field].strip()

            if field == "account_id":
                entity = Account.objects.get(id=field_data)
                setattr(package, "account", entity)
            elif field == "carrier_id":
                entity = Carrier.objects.get(id=field_data)
                setattr(package, "carrier", entity)
            elif field == "package_type_id":
                entity = PackageType.objects.get(id=field_data)
                setattr(package, "package_type", entity)
            elif field == "comments" and package_data[field] is None:
                setattr(package, field, "")
            elif field == "price":
                field_data = type_func(field_data)
                if package.price == field_data:
                    continue

                # Calculate the change in price
                change_in_price = package.price - field_data
                if change_in_price > 0:
                    credit = change_in_price
                    debit = 0
                else:
                    credit = 0
                    debit = change_in_price * -1

                # Update the balance for the account
                account_id = package.account_id

                if account_id in accounts:
                    account = accounts[account_id]
                    account.balance += change_in_price
                else:
                    current_balance = Account.objects.filter(pk=package.account_id).values_list(
                                                             "balance", flat=True).first()
                    if current_balance is not None:
                        new_balance = current_balance + change_in_price
                        account = Account(id=package.account_id, balance=new_balance)
                        accounts[account_id] = account

                if not no_ledger:
                    # Create the new ledger entry for the price change
                    acct_entry = AccountLedger(user_id=user.id, package_id=package.id,
                                               account_id=package.account_id, debit=debit,
                                               credit=credit, description="Price changed", is_late=False)
                    account_ledger.append(acct_entry)

                setattr(package, field, type_func(field_data))
            else:
                setattr(package, field, type_func(field_data))
        updates.append(package)

    if updates:
        Package.objects.bulk_update(updates, package_data.keys())

    if accounts:
        accounts_to_update = list(accounts.values())
        Account.objects.bulk_update(accounts_to_update, ["balance"])

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

        Package.objects.filter(id__in=ids).update(current_state=state)

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
