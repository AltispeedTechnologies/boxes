import re
from .common import _get_packages, _search_packages_helper
from boxes.forms import PackageForm
from boxes.models import *
from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods


def all_packages(request):
    # Only get checked in packages
    packages = _get_packages()

    # Paginate
    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "packages/index.html", {"search_url": reverse("search_packages"),
                                                   "page_obj": page_obj})

def package_detail(request, pk):
    package_values = Package.objects.select_related("account", "carrier", "packagetype").values(
        "id",
        "price",
        "carrier__name",
        "account__description",
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
            debit, credit = (0, pkg["price"]) if debit_credit_switch else (pkg["price"], 0)
            acct_entry = AccountLedger(user_id=request.user.id, package_id=pkg["id"],
                                       account_id=pkg["account_id"], debit=debit, credit=credit, description="")
            pkg_entry = PackageLedger(user_id=request.user.id, package_id=pkg["id"], state=state)
            account_ledger.append(acct_entry)
            package_ledger.append(pkg_entry)
            affected_accounts.add(pkg["account_id"])

        AccountLedger.objects.bulk_create(account_ledger)
        PackageLedger.objects.bulk_create(package_ledger)

        # Update balances for affected accounts
        accounts = Account.objects.filter(id__in=affected_accounts).annotate(
            total_credit=Sum("accountledger__credit", default=0),
            total_debit=Sum("accountledger__debit", default=0)
        )
        for account in accounts:
            new_balance = account.total_credit - account.total_debit
            if new_balance != account.balance:
                account.balance = new_balance
                account.save(update_fields=["balance"])

        response_data["success"] = True
        return response_data
    except ValidationError as e:
        response_data["errors"] = [str(message) for message in e.messages]
    except Exception as e:
        response_data["errors"] = [str(e)]
    return response_data

def check_in_packages(request):
    if request.method == "POST":
        result = update_packages_util(request, state=1, debit_credit_switch=False)
        if result["success"]:
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occurred."])})

def check_out_packages(request):
    if request.method == "POST":
        result = update_packages_util(request, state=2, debit_credit_switch=True)
        if result["success"]:
            messages.success(request, "Successfully checked out")
            return JsonResponse({"success": True, "redirect_url": reverse("check_out_packages")})
        else:
            messages.error(request, "Checkout failed")
            return JsonResponse({"success": False, "errors": result.get("errors", ["An unknown error occurred."])})
    else:
        return render(request, "packages/check_out.html", {"search_url": reverse("search_check_out_packages")})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.POST)
        if form.is_valid():
            print(request.POST)
            package = form.save(commit=False)
            package.carrier_id = form.cleaned_data["carrier_id"]
            package.account_id = form.cleaned_data["account_id"]
            package.package_type_id = form.cleaned_data["package_type_id"]
            package.save()
            return JsonResponse({"success": True, "id": package.id})
        else:
            errors = dict(form.errors.items()) if form.errors else {}
            return JsonResponse({"success": False, "errors": errors})
    else:
        form = PackageForm()
        return render(request, "packages/create.html", {"form": form})

def search_check_out_packages(request):
    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("packages")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    selected_ids = request.GET.get("selected_ids", "")
    selected = selected_ids.split(",") if selected_ids else []
    query = request.GET.get("q", "")
    filter_info = request.GET.get("filter", "")

    return render(request, "packages/search_checkout.html", {"checkout": True,
                                                             "page_obj": page_obj,
                                                             "selected": selected,
                                                             "query": query,
                                                             "filter": filter_info})

@require_http_methods(["GET"])
def type_search(request):
    search_query = request.GET.get("term", "")
    pkgtypes = PackageType.objects.filter(description__icontains=search_query)[:10]
    results = [{"id": pkgtype.id, "text": pkgtype.description} for pkgtype in pkgtypes]
    return JsonResponse({"results": results})

def search_packages(request):
    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("packages")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    # Enable a card with the user information if the filter is customer
    account = None
    if request.GET.get("filter", "").strip() == "customer":
        account_id_raw = request.GET.get("cid", "").strip()
        account_id = re.sub(r'\D', '', account_id_raw)
        
        if account_id:
            account = Account.objects.get(id=account_id)

    return render(request, "packages/search.html", {"page_obj": page_obj,
                                                    "query": request.GET.get("q", ""),
                                                    "filter": request.GET.get("filter", ""),
                                                    "account": account})

