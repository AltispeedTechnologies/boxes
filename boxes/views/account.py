import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import Account, AccountLedger
from .common import _get_packages, _get_matching_users

@require_http_methods(["GET"])
def account_search(request):
    search_query = request.GET.get("term", "")
    accounts = Account.objects.filter(name__icontains=search_query)[:10]
    results = [{"id": account.id, "text": account.name} for account in accounts]
    return JsonResponse({"results": results})

@require_http_methods(["GET"])
def account_edit(request, pk):
    user, account = _get_matching_users(pk)
    return render(request, "accounts/edit.html", {"custom_user": user,
                                                  "account": account,
                                                  "view_type": "edit"})

@require_http_methods(["GET"])
def account_ledger(request, pk):
    account = Account.objects.filter(id=pk).first()
    ledger = AccountLedger.objects.select_related("user", "package").values(
        "credit",
        "debit",
        "timestamp",
        "description",
        "package_id",
        "user__first_name",
        "user__last_name",
        "package__tracking_code"
    ).filter(account_id=pk).order_by("-timestamp")

    paginator = Paginator(ledger, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/account.html", {"account": account,
                                                     "page_obj": page_obj,
                                                     "account_id": pk,
                                                     "view_type": "ledger"})

@require_http_methods(["GET"])
def account_packages(request, pk):
    account = Account.objects.filter(id=pk).first()
    packages = _get_packages(account__id=account.id)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "accounts/packages.html", {"account": account,
                                                      "page_obj": page_obj,
                                                      "view_type": "packages"})

@require_http_methods(["POST"])
def update_account(request, pk):
    print(request.body)
    request_data = json.loads(request.body)
    account = get_object_or_404(Account, pk=pk)

    fields_to_update = {
        "balance": float,
        "is_good_standing": bool,
        "name": str,
        "comments": str
    }

    try:
        updates = {}
        for field, type_func in fields_to_update.items():
            value = request_data.get(field)
            if value != None:
                updates[field] = type_func(value.strip())

        for field, value in updates.items():
            setattr(account, field, value)
        
        if updates:
            account.save()

        return JsonResponse({"success": True})

    except (ValueError, Decimal.InvalidOperation, TypeError) as e:
        return JsonResponse({"success": False, "errors": [f"Error updating {field}: {str(e)}"]})
