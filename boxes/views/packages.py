import json
import re
from .common import _get_packages, _search_packages_helper
from boxes.forms import PackageForm
from boxes.models import *
from boxes.tasks import total_accounts
from decimal import Decimal
from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.http import require_http_methods


def get_or_create_account(account_id, user):
    if not account_id.isdigit():
        account, _ = Account.objects.get_or_create(user=user, balance=Decimal(0.00), is_good_standing=True, name=strip_tags(account_id))
        return account
    return Account.objects.get(id=account_id)

def all_packages(request):
    return render(request, "packages/index.html", {"search_url": reverse("search_packages")})

def package_detail(request, pk):
    package_values = Package.objects.select_related("account", "carrier", "packagetype").values(
        "id",
        "price",
        "carrier__name",
        "account__name",
        "package_type__description",
        "tracking_code",
        "comments",
    ).filter(id=pk).first()

    state_ledger = PackageLedger.objects.select_related("user").values(
        "user__first_name",
        "user__last_name",
        "state",
        "timestamp",
    ).filter(package_id=pk)

    state_names = dict(PACKAGE_STATES)
    for entry in state_ledger:
        entry["state"] = state_names.get(entry["state"], "Unknown")

    return render(request, "packages/package.html", {"package": package_values,
                                                     "state_ledger": state_ledger})

def update_packages_util(request, state, debit_credit_switch=False):
    response_data = {"success": False, "errors": []}
    try:
        ids = request.POST.getlist("ids[]", [])
        if not ids:
            raise ValueError("No package IDs provided.")

        Package.objects.filter(id__in=ids).update(current_state=state)
        account_ledger, package_ledger, affected_accounts = [], [], set()
        for pkg in Package.objects.filter(id__in=ids).values("id", "account_id", "price"):
            pkg_entry = PackageLedger(user_id=request.user.id, package_id=pkg["id"], state=state)
            package_ledger.append(pkg_entry)

            if pkg["price"] == 0:
                continue

            debit, credit = (0, pkg["price"]) if debit_credit_switch else (pkg["price"], 0)
            acct_entry = AccountLedger(user_id=request.user.id, package_id=pkg["id"],
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

@require_http_methods(["POST"])
def check_in_packages(request):
    queue_id = request.POST.get("queue_id")
    PackageQueue.objects.filter(queue_id=queue_id).delete()

    result = update_packages_util(request, state=1, debit_credit_switch=False)
    ids = request.POST.getlist("ids[]", [])
    check_in_template = EmailSettings.objects.values_list("check_in_template", flat=True).first()
    for package_id in ids:
        EmailQueue.objects.create(package_id=package_id, template_id=check_in_template)

    if result["success"]:
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occurred."])})


@require_http_methods(["POST"])
def check_out_packages(request):
    result = update_packages_util(request, state=2, debit_credit_switch=True)
    if result["success"]:
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occurred."])})

@require_http_methods(["POST"])
def check_out_packages_reverse(request):
    result = update_packages_util(request, state=1, debit_credit_switch=False)
    if result["success"]:
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occurred."])})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)

            queue_id = form.cleaned_data["queue_id"]
            
            # Use helper functions
            package.carrier = Carrier.objects.get(id=form.cleaned_data["carrier_id"])
            package.account = get_or_create_account(form.cleaned_data["account_id"], request.user)
            package.package_type = PackageType.objects.get(id=form.cleaned_data["package_type_id"])

            try:
                package.save()
                PackageQueue.objects.create(package=package, queue_id=queue_id)
                return JsonResponse({"success": True, "id": package.id})
            except Exception as e:
                return JsonResponse({"success": False, "errors": str(e)})
        else:
            return JsonResponse({"success": False, "form_errors": form.errors})
    else:
        form = PackageForm()
        queues = Queue.objects.filter(check_in=True)
        prices = PackageType.objects.all().values_list("default_price", flat=True)
        return render(request, "packages/create.html", {"form": form,
                                                        "queues": queues,
                                                        "prices": prices})

@require_http_methods(["GET"])
def queue_packages(request, pk):
    packages = PackageQueue.objects.filter(queue=pk).select_related(
        "package__account",
        "package__package_type",
        "package__carrier"
    ).values(
        "package__id", 
        "package__account__name",
        "package__account__id",
        "package__tracking_code",
        "package__price",
        "package__carrier__name",
        "package__carrier__id",
        "package__package_type__description",
        "package__package_type__id",
        "package__inside",
        "package__comments"
    )

    # Prepare the packages list with appropriate key names
    packages_list = [
        {
            "id": package["package__id"],
            "account": package["package__account__name"],
            "account_id": package["package__account__id"],
            "tracking_code": package["package__tracking_code"],
            "price": package["package__price"],
            "carrier": package["package__carrier__name"],
            "carrier_id": package["package__carrier__id"],
            "package_type": package["package__package_type__description"],
            "package_type_id": package["package__package_type__id"],
            "inside": package["package__inside"],
            "comments": package["package__comments"],
        } for package in packages
    ]

    return JsonResponse({"success": True, "packages": packages_list})

@require_http_methods(["POST"])
def update_queue_name(request, pk):
    try:
        data = json.loads(request.body)
        queue_id = data["id"]
        description = data["description"]

        queue = get_object_or_404(Queue, pk=queue_id)

        queue.description = description
        queue.save()

        return JsonResponse({"success": True})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except KeyError:
        return JsonResponse({"success": False, "message": "Missing id or description in payload"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error updating queue: {str(e)}"}, status=500)

def update_packages_fields(package_ids, package_data, user):
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
        try:
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
                    entity = get_or_create_account(field_data, user)
                    setattr(package, "account", entity)
                elif field == "carrier_id":
                    entity = Carrier.objects.get(id=field_data)
                    setattr(package, "carrier", entity)
                elif field == "package_type_id":
                    entity = PackageType.objects.get(id=package_type_id)
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
                        current_balance = Account.objects.filter(pk=package.account_id).values_list("balance", flat=True).first()
                        if current_balance is not None:
                            new_balance = current_balance + change_in_price
                            account = Account(id=package.account_id, balance=new_balance)
                            accounts[account_id] = account

                    # Create the new ledger entry for the price change
                    acct_entry = AccountLedger(user_id=user.id, package_id=package.id,
                                               account_id=package.account_id, debit=debit, 
                                               credit=credit, description="")
                    account_ledger.append(acct_entry)

                    setattr(package, field, type_func(field_data))
                else:
                    setattr(package, field, type_func(field_data))
            updates.append(package)
        except (ValueError, Decimal.InvalidOperation, TypeError) as e:
            errors.append(f"Error updating Package ID {package.pk}: {str(e)}")

    if updates:
        Package.objects.bulk_update(updates, package_data.keys())

    if accounts:
        accounts_to_update = list(accounts.values())
        Account.objects.bulk_update(accounts_to_update, ["balance"])

    if account_ledger:
        AccountLedger.objects.bulk_create(account_ledger)

    if errors:
        return {"success": False, "errors": errors}
    return {"success": True}

@require_http_methods(["POST"])
def update_package(request, pk):
    request_data = json.loads(request.body)
    result = update_packages_fields([pk], request_data, request.user)
    return JsonResponse(result)

@require_http_methods(["POST"])
def update_packages(request):
    request_data = json.loads(request.body)
    package_ids = request_data.get("ids")
    package_data = request_data.get("values")
    print(request_data)

    result = update_packages_fields(package_ids, package_data, request.user)
    return JsonResponse(result)

@require_http_methods(["GET"])
def type_search(request):
    search_query = request.GET.get("term", "")
    pkgtypes = PackageType.objects.filter(description__icontains=search_query)[:10]
    results = [{"id": pkgtype.id,
                "text": pkgtype.description,
                "default_price": pkgtype.default_price} for pkgtype in pkgtypes]
    return JsonResponse({"results": results})

@require_http_methods(["GET"])
def search_packages(request):
    req_filter = request.GET.get("filter").strip()
    if req_filter not in ["tracking_code", ""]:
        return

    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("packages")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []

    return render(request, "packages/search.html", {"page_obj": page_obj,
                                                    "query": request.GET.get("q", ""),
                                                    "filter": request.GET.get("filter", ""),
                                                    "selected": selected,
                                                    "account_packages": True})

