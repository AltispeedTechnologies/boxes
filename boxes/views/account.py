import json
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.paginator import Paginator
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from boxes.models import Account, AccountAlias, AccountLedger, SentEmail, SentEmailContents, SentEmailPackage, SentEmailResult
from .common import _get_packages, _get_matching_users

@require_http_methods(["GET"])
def account_search(request):
    search_query = request.GET.get("term", "")
    aliases = AccountAlias.objects.filter(alias__icontains=search_query)[:10]
    results = [{"id": alias.account.id,
                "text": alias.alias,
                "billable": alias.account.billable} for alias in aliases]
    return JsonResponse({"results": results})

@require_http_methods(["GET"])
def account_edit(request, pk):
    user, account = _get_matching_users(pk)
    aliases = AccountAlias.objects.filter(account_id=pk)
    return render(request, "accounts/edit.html", {"custom_user": user,
                                                  "account": account,
                                                  "aliases": aliases,
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

    paginator = Paginator(ledger, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/account.html", {"account": account,
                                                     "page_obj": page_obj,
                                                     "account_id": pk,
                                                     "view_type": "ledger"})

@require_http_methods(["GET"])
def account_packages(request, pk):
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()
    packages = _get_packages(account__id=account.id)

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "accounts/packages.html", {"account": account,
                                                      "page_obj": page_obj,
                                                      "view_type": "packages"})
@require_http_methods(["GET"])
def account_emails(request, pk):
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()
    emails = SentEmail.objects.filter(account=account).annotate(
        sent_id=F("pk"),
        timestamp_val=F("timestamp"),
        subject_val=F("subject"),
        email_val=F("email"),
        status=F("success"),
        tracking_codes=ArrayAgg(
            Concat(
                F("sentemailpackage__package__id"),
                Value(" "),
                F("sentemailpackage__package__tracking_code"),
                output_field=CharField()
            ),
            distinct=True,
            filter=Q(sentemailpackage__package__isnull=False)
        )
    ).order_by("-timestamp_val")
    for email in emails:
        tracking_codes = [
            [int(part) if i == 0 else part for i, part in enumerate(code.split(" ", 1))] 
            for code in email.tracking_codes
        ]
        email.tracking_codes = tracking_codes

    page_number = request.GET.get("page")
    paginator = Paginator(emails, 15)
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/emails.html", {"account": account,
                                                    "page_obj": page_obj,
                                                    "enable_tracking_codes": True,
                                                    "view_type": "emails"})

@require_http_methods(["POST"])
def update_account(request, pk):
    request_data = json.loads(request.body)
    account = get_object_or_404(Account, pk=pk)

    fields_to_update = {
        "balance": float,
        "billable": bool,
        "name": str,
        "comments": str
    }

    try:
        updates = {}
        for field, type_func in fields_to_update.items():
            value = request_data.get(field)
            if value != None and type_func != bool:
                updates[field] = type_func(value.strip())
            elif value != None:
                updates[field] = type_func(value)

        for field, value in updates.items():
            setattr(account, field, value)
        
        if updates:
            account.save()

        return JsonResponse({"success": True})

    except (ValueError, Decimal.InvalidOperation, TypeError) as e:
        return JsonResponse({"success": False, "errors": [f"Error updating {field}: {str(e)}"]})

@require_http_methods(["POST"])
def update_package_aliases(request):
    try:
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
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "errors": "Invalid JSON"})
    except Account.DoesNotExist:
        return JsonResponse({"success": False, "errors": "Account not found"})
