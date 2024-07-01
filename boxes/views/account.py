import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import (Account, AccountAlias, AccountLedger, CustomUserEmail, SentEmail, SentEmailContents,
                          SentEmailPackage, SentEmailResult)
from boxes.management.exception_catcher import exception_catcher
from boxes.views.common import _get_packages, _get_matching_users, _get_emails


@require_http_methods(["GET"])
def account_search(request):
    search_query = request.GET.get("term", "")
    aliases = AccountAlias.objects.filter(alias__icontains=search_query)[:10]
    results = [{"id": alias.account.id,
                "text": alias.alias,
                "billable": alias.account.billable} for alias in aliases]
    return JsonResponse({"success": True, "results": results})


@require_http_methods(["GET"])
def account_edit(request, pk):
    user, account = _get_matching_users(pk)
    aliases = AccountAlias.objects.filter(account_id=pk)
    emails = CustomUserEmail.objects.filter(user=user)
    return render(request, "accounts/edit.html", {"custom_user": user,
                                                  "account": account,
                                                  "aliases": aliases,
                                                  "emails": emails,
                                                  "view_type": "edit"})


@require_http_methods(["GET"])
def account_ledger(request, pk):
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()
    ledger = AccountLedger.objects.select_related("user", "package").values(
        "credit",
        "debit",
        "timestamp",
        "description",
        "package_id",
        "is_late",
        "user__first_name",
        "user__last_name",
        "package__tracking_code"
    ).filter(account_id=pk).order_by("-timestamp")

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(ledger, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/account.html", {"account": account,
                                                     "page_obj": page_obj,
                                                     "account_id": pk,
                                                     "view_type": "ledger"})


@require_http_methods(["GET"])
def account_packages(request, pk):
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    packages = _get_packages(per_page=per_page, account__id=account.id)
    page_obj = packages.get_page(page_number)

    return render(request, "accounts/packages.html", {"account": account,
                                                      "page_obj": page_obj,
                                                      "view_type": "packages"})


@require_http_methods(["GET"])
def account_emails(request, pk):
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    page_obj = _get_emails(per_page, page_number, account=account)

    return render(request, "accounts/emails.html", {"account": account,
                                                    "page_obj": page_obj,
                                                    "enable_tracking_codes": True,
                                                    "view_type": "emails"})


@require_http_methods(["POST"])
@exception_catcher()
def update_account(request, pk):
    request_data = json.loads(request.body)
    account = get_object_or_404(Account, pk=pk)

    fields_to_update = {
        "balance": float,
        "billable": bool,
        "name": str,
        "comments": str
    }

    updates = {}
    for field, type_func in fields_to_update.items():
        value = request_data.get(field)
        if value is not None and type_func is not bool:
            updates[field] = type_func(value.strip())
        elif value is not None:
            updates[field] = type_func(value)

    for field, value in updates.items():
        setattr(account, field, value)

    if updates:
        account.save()


@require_http_methods(["POST"])
@exception_catcher()
def update_account_aliases(request):
    data = json.loads(request.body)
    updated_aliases = dict()

    for account_id, aliases in data.items():
        for key, value in aliases.items():
            if key.startswith("NEW_"):
                new_alias = AccountAlias(account_id=account_id, alias=value, primary=False)
                new_alias.save()
                updated_aliases[key] = new_alias.id
            elif key.startswith("REMOVE_"):
                alias_id = int(key[7:])
                alias = AccountAlias.objects.get(id=alias_id, account_id=account_id)
                alias.delete()
                updated_aliases[key] = True
            else:
                alias = AccountAlias.objects.get(id=int(key), account_id=account_id)
                alias.alias = value
                alias.save()

    return JsonResponse({"success": True, "aliases": updated_aliases})
