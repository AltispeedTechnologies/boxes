"""Staff account detail: search, ledger, packages, emails, updates, memberships."""
import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from boxes.backend.account import create_web_user, ensure_account_balance
from boxes.backend.membership import associate_user, disassociate_user, search_users
from boxes.management.exception_catcher import exception_catcher
from boxes.models import (
    Account,
    AccountAlias,
    AccountLedger,
    CustomUser,
    CustomUserEmail,
    UserAccount,
)
from boxes.views.common import _get_emails, _get_matching_users, _get_packages


@require_http_methods(["GET"])
def account_search(request):
    """JSON/Select2 search over accounts and aliases."""
    search_query = request.GET.get("term", "")
    aliases = AccountAlias.objects.filter(alias__icontains=search_query)[:10]
    results = [{
        "id": alias.account.id,
        "text": alias.alias,
        "billable": alias.account.billable,
    } for alias in aliases]
    return JsonResponse({"success": True, "results": results})


@require_http_methods(["GET"])
def user_search(request):
    """JSON/Select2 search over users for membership linking."""
    term = request.GET.get("term", "") or request.GET.get("q", "")
    users = search_users(term, limit=20)
    results = [{
        "id": u.id,
        "text": f"{u.username} — {u.first_name} {u.last_name}".strip(" —"),
        "username": u.username,
        "is_active": u.is_active,
    } for u in users]
    return JsonResponse({"success": True, "results": results})


@require_http_methods(["GET"])
def account_edit(request, pk):
    """Render staff account edit page."""
    users, account = _get_matching_users(pk)
    ensure_account_balance(account)
    aliases = AccountAlias.objects.filter(account_id=pk)
    memberships = (
        UserAccount.objects.filter(account=account)
        .select_related("user")
        .order_by("-is_active", "role", "user__username")
    )
    custom_user = users[0] if users else None
    emails = CustomUserEmail.objects.filter(user=custom_user) if custom_user else []
    return render(request, "accounts/edit.html", {
        "custom_user": custom_user,
        "custom_users": users,
        "memberships": memberships,
        "account": account,
        "aliases": aliases,
        "emails": emails,
        "view_type": "edit",
    })


@require_http_methods(["POST"])
@exception_catcher()
def account_members_link(request, pk):
    """POST (staff): link a user to this account by user_id or username."""
    account = get_object_or_404(Account, pk=pk)
    data = json.loads(request.body) if request.body else {}
    user_id = data.get("user_id") or request.POST.get("user_id")
    username = (data.get("username") or request.POST.get("username") or "").strip()

    if user_id is not None and str(user_id).strip() != "":
        user = get_object_or_404(CustomUser, pk=user_id)
    elif username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        raise ValueError("user_id or username is required")

    role = data.get("role") or request.POST.get("role") or UserAccount.ROLE_MEMBER
    try:
        membership = associate_user(account, user, role=role, actor=request.user)
    except ValidationError as exc:
        return JsonResponse({"success": False, "errors": exc.messages}, status=400)

    return JsonResponse({
        "success": True,
        "membership": {
            "id": membership.id,
            "user_id": membership.user_id,
            "account_id": membership.account_id,
            "role": membership.role,
            "is_active": membership.is_active,
        },
    })


@require_http_methods(["POST"])
@exception_catcher()
def account_members_disassociate(request, pk):
    """POST (staff): soft-disassociate a user from this account by user_id."""
    account = get_object_or_404(Account, pk=pk)
    data = json.loads(request.body) if request.body else {}
    user_id = data.get("user_id") or request.POST.get("user_id")
    if user_id is None:
        raise ValueError("user_id is required")
    user = get_object_or_404(CustomUser, pk=user_id)
    allow_last = bool(data.get("allow_last_owner") or request.POST.get("allow_last_owner"))
    try:
        membership = disassociate_user(
            account, user, actor=request.user, allow_last_owner=allow_last
        )
    except ValidationError as exc:
        return JsonResponse({"success": False, "errors": list(exc.messages)}, status=400)
    if membership is None:
        return JsonResponse({"success": False, "errors": ["Membership not found"]}, status=404)
    return JsonResponse({
        "success": True,
        "membership": {
            "id": membership.id,
            "user_id": membership.user_id,
            "account_id": membership.account_id,
            "role": membership.role,
            "is_active": membership.is_active,
        },
    })


@require_http_methods(["POST"])
@exception_catcher()
def account_members_create_web(request, pk):
    """POST (staff): create a new web portal login and link it to this account.

    Body JSON: username, password, first_name (required), last_name, email,
    role (owner|member, default owner), is_active (default true), phone fields.
    """
    account = get_object_or_404(Account, pk=pk)
    data = json.loads(request.body) if request.body else {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or data.get("password1") or ""
    password2 = data.get("password2")
    if password2 is not None and password and password != password2:
        return JsonResponse({
            "success": False,
            "form_errors": {"password": ["Passwords do not match."]},
        })

    role = data.get("role") or UserAccount.ROLE_OWNER
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    if not first_name and account.name:
        parts = account.name.split()
        first_name = parts[0]
        if not last_name and len(parts) > 1:
            last_name = " ".join(parts[1:])
    elif not last_name and account.name:
        parts = account.name.split()
        if len(parts) > 1:
            last_name = " ".join(parts[1:])

    try:
        user, membership = create_web_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            middle_name=(data.get("middle_name") or "").strip(),
            prefix=(data.get("prefix") or "").strip(),
            suffix=(data.get("suffix") or "").strip(),
            company=(data.get("company") or "").strip(),
            phone_number=(data.get("phone_number") or "").strip(),
            mobile_number=(data.get("mobile_number") or "").strip(),
            email=(data.get("email") or "").strip() or None,
            is_active=bool(data.get("is_active", True)),
            account=account,
            role=role,
            actor=request.user,
        )
    except ValidationError as exc:
        errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": list(exc.messages)}
        return JsonResponse({"success": False, "form_errors": errors})

    return JsonResponse({
        "success": True,
        "user_id": user.id,
        "username": user.username,
        "membership": {
            "id": membership.id,
            "user_id": membership.user_id,
            "account_id": membership.account_id,
            "role": membership.role,
            "is_active": membership.is_active,
        },
    })


@require_http_methods(["GET"])
def account_ledger(request, pk):
    """Render or return ledger rows for an account."""
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()
    ledger = AccountLedger.objects.select_related("user", "package", "invoice").values(
        "credit",
        "debit",
        "timestamp",
        "description",
        "package_id",
        "is_late",
        "user__first_name",
        "user__last_name",
        "package__tracking_code",
        "invoice__id",
    ).filter(account_id=pk).order_by("-timestamp")

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(ledger, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/account.html", {
        "account": account,
        "page_obj": page_obj,
        "account_id": pk,
        "view_type": "ledger",
    })


@require_http_methods(["GET"])
def account_packages(request, pk):
    """List packages belonging to an account."""
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    packages = _get_packages(per_page=per_page, account__id=account.id)
    page_obj = packages.get_page(page_number)

    return render(request, "accounts/packages.html", {
        "account": account,
        "page_obj": page_obj,
        "view_type": "packages",
    })


@require_http_methods(["GET"])
def account_emails(request, pk):
    """List sent emails related to an account."""
    account = Account.objects.filter(id=pk).select_related("accountbalance").first()

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    page_obj = _get_emails(per_page, page_number, account=account)

    return render(request, "accounts/emails.html", {
        "account": account,
        "page_obj": page_obj,
        "enable_tracking_codes": True,
        "view_type": "emails",
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_account(request, pk):
    """POST: update account fields (name, billable, comments, etc.)."""
    request_data = json.loads(request.body)
    account = get_object_or_404(Account, pk=pk)

    fields_to_update = {
        "balance": float,
        "billable": bool,
        "name": str,
        "comments": str,
    }

    updates = {}
    for field, type_func in fields_to_update.items():
        value = request_data.get(field)
        if value is None:
            continue
        if type_func is bool:
            if isinstance(value, str):
                updates[field] = value.lower() in ("1", "true", "yes", "on")
            else:
                updates[field] = bool(value)
        elif type_func is str:
            updates[field] = type_func(str(value).strip())
        else:
            updates[field] = type_func(value)

    for field, value in updates.items():
        setattr(account, field, value)

    if updates:
        account.save()
        if "name" in updates:
            account.ensure_primary_alias()

    return JsonResponse({
        "success": True,
        "account_id": account.id,
        "updated": list(updates.keys()),
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_account_aliases(request):
    """POST: replace/update account alias list."""
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


@require_http_methods(["POST"])
@exception_catcher()
def account_fee_waiver(request, pk):
    """POST: staff credit waiver on account ledger (account_id from URL).

    Body (JSON or form): amount (required, > 0), description (optional).
    Creates an AccountLedger credit and recalculates balances.
    """
    from boxes.tasks import total_accounts

    account = get_object_or_404(Account, pk=pk)
    if request.content_type and "application/json" in request.content_type:
        data = json.loads(request.body) if request.body else {}
    else:
        data = request.POST

    amount_raw = data.get("amount")
    if amount_raw is None or str(amount_raw).strip() == "":
        raise ValueError("amount is required")
    amount = Decimal(str(amount_raw).strip())
    if amount <= 0:
        raise ValueError("amount must be positive")

    description = data.get("description") or "Fee waiver"
    description = str(description).strip()[:256]

    entry = AccountLedger.objects.create(
        user=request.user,
        account=account,
        credit=amount,
        debit=Decimal("0.00"),
        description=description,
        package=None,
        invoice=None,
        is_late=False,
    )
    total_accounts.delay(account_id=account.id)
    return JsonResponse({
        "success": True,
        "ledger_id": entry.id,
        "credit": str(entry.credit),
        "description": entry.description,
    })
