"""Profile self-service and staff user create/update endpoints."""
import json

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods

from boxes.backend.account import create_account_with_web_user, create_billing_account, ensure_customer_group
from boxes.backend.membership import associate_user
from boxes.forms import CustomUserForm
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Account, CustomUser, CustomUserEmail, UserAccount


@require_http_methods(["GET"])
def profile_user(request):
    """Self-service profile for the logged-in CustomUser.

    CustomUser is the login identity. Account is a separate billing/parcel
    entity linked through UserAccount. Profile edits only touch the user
    (and notification emails). If the user is linked to exactly one Account,
    name changes are mirrored onto that account's display name / primary
    alias — the same rule staff edit uses.
    """
    user = CustomUser.objects.get(pk=request.user.pk)
    emails = CustomUserEmail.objects.filter(user=user).order_by("id")
    linked_accounts = (
        Account.objects.filter(user_memberships__user=user, user_memberships__is_active=True)
        .select_related("accountbalance")
        .distinct()
        .order_by("name")
    )
    return render(request, "profile.html", {
        "custom_user": user,
        "emails": emails,
        "linked_accounts": linked_accounts,
    })


def _sync_single_account_name(user, user_data):
    """If the user maps to exactly one Account, keep its display name in sync."""
    account_ids = list(
        UserAccount.objects.filter(user=user, is_active=True).values_list("account_id", flat=True)
    )
    if len(account_ids) != 1:
        return

    new_account_name = " ".join(
        user_data.get(field, "") or ""
        for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"]
        if user_data.get(field)
    ).strip()
    if not new_account_name:
        return

    account = Account.objects.filter(pk=account_ids[0]).first()
    if not account:
        return

    account.name = new_account_name
    account.save()
    account.ensure_primary_alias()


@require_http_methods(["POST"])
@exception_catcher()
def update_profile(request):
    """Update the authenticated user's profile fields (and optional password)."""
    data = json.loads(request.body)
    user = CustomUser.objects.get(pk=request.user.pk)

    # Password change is optional; handled separately from CustomUserForm
    new_password1 = (data.pop("new_password1", None) or "").strip()
    new_password2 = (data.pop("new_password2", None) or "").strip()

    # Never allow client to target another user
    data.pop("id", None)
    data.pop("pk", None)

    form = CustomUserForm(data, instance=user)
    if not form.is_valid():
        return JsonResponse({"success": False, "form_errors": form.errors})

    password_errors = []
    if new_password1 or new_password2:
        if new_password1 != new_password2:
            password_errors.append("Passwords do not match.")
        else:
            try:
                validate_password(new_password1, user=user)
            except ValidationError as exc:
                password_errors.extend(list(exc.messages))

    if password_errors:
        return JsonResponse({"success": False, "form_errors": {"new_password1": password_errors}})

    with transaction.atomic():
        form.save()
        _sync_single_account_name(user, form.cleaned_data)
        if new_password1:
            user.set_password(new_password1)
            user.save(update_fields=["password"])
            update_session_auth_hash(request, user)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@exception_catcher()
def update_profile_emails(request):
    """Create/update/remove CustomUserEmail rows for the authenticated user only."""
    data = json.loads(request.body)
    user_id = request.user.pk
    # Payload is a flat map of email row keys -> values for this user
    emails = data.get("emails", data)
    updated_emails = {}

    for key, value in emails.items():
        if key.startswith("NEW_"):
            value = (value or "").strip()
            if not value:
                continue
            new_email = CustomUserEmail(user_id=user_id, email=value)
            new_email.save()
            updated_emails[key] = new_email.id
        elif key.startswith("REMOVE_"):
            email_id = int(key[7:])
            email = CustomUserEmail.objects.get(id=email_id, user_id=user_id)
            email.delete()
            updated_emails[key] = True
        else:
            email = CustomUserEmail.objects.get(id=int(key), user_id=user_id)
            email.email = (value or "").strip()
            email.save()
            updated_emails[key] = email.id

    return JsonResponse({"success": True, "emails": updated_emails})


@require_http_methods(["POST"])
@exception_catcher()
def update_user(request):
    """POST (staff): update a target user's profile fields."""
    data = json.loads(request.body)

    for user_id, user_data in data.items():
        accounts = list(
            UserAccount.objects.filter(user=user_id, is_active=True).values_list("account_id", flat=True)
        )
        if len(accounts) == 1:
            new_account_name = ""
            for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"]:
                val = user_data.get(field) or ""
                if val:
                    new_account_name += val + " "

            account = Account.objects.filter(pk=accounts[0]).first()
            if account:
                account.name = new_account_name.strip()
                account.save()
                account.ensure_primary_alias()

        user = CustomUser.objects.get(id=user_id)
        form = CustomUserForm(user_data, instance=user)
        if form.is_valid():
            form.save()
        else:
            return JsonResponse({"success": False, "form_errors": form.errors})

    return JsonResponse({"success": True})


def generate_username():
    """Generate a unique username string for new users."""
    while True:
        username = get_random_string(32)
        if not CustomUser.objects.filter(username=username).exists():
            return username


@require_http_methods(["POST"])
@exception_catcher()
def create_user(request):
    """POST (staff): create billing account + optional portal web login.

    Body JSON:
      - name fields (first_name required unless username-only legacy path)
      - company, phone_number, email
      - username / password: when both provided, create an active web login
      - create_web_account (bool): force web login; requires username+password
      - billable (bool, default true)
      - comments

    Without username+password, creates a billing Account with an inactive
    placeholder membership user (legacy check-in path).
    """
    data = json.loads(request.body) if request.body else {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    middle_name = (data.get("middle_name") or "").strip()
    prefix = (data.get("prefix") or "").strip()
    suffix = (data.get("suffix") or "").strip()
    company = (data.get("company") or "").strip()
    phone_number = (data.get("phone_number") or data.get("phone") or "").strip()
    mobile_number = (data.get("mobile_number") or "").strip()
    email = (data.get("email") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or data.get("password1") or ""
    password2 = data.get("password2")
    create_web = bool(data.get("create_web_account") or data.get("web_account"))
    billable = data.get("billable", True)
    if isinstance(billable, str):
        billable = billable.lower() in ("1", "true", "yes", "on")
    comments = data.get("comments")
    account_name = (data.get("account_name") or data.get("name") or "").strip()

    # Explicit web account creation (or username+password provided)
    wants_web = create_web or (username and password)
    if create_web and (not username or not password):
        return JsonResponse({
            "success": False,
            "form_errors": {
                "username": ["Username is required for web accounts."] if not username else [],
                "password": ["Password is required for web accounts."] if not password else [],
            },
        })

    if password2 is not None and password and password != password2:
        return JsonResponse({
            "success": False,
            "form_errors": {"password": ["Passwords do not match."]},
        })

    if not first_name and not account_name:
        return JsonResponse({
            "success": False,
            "form_errors": {"first_name": ["First name is required."]},
        })

    if wants_web:
        try:
            result = create_account_with_web_user(
                actor=request.user,
                username=username,
                password=password,
                first_name=first_name or username,
                last_name=last_name,
                middle_name=middle_name,
                prefix=prefix,
                suffix=suffix,
                company=company,
                phone_number=phone_number,
                mobile_number=mobile_number,
                email=email or None,
                account_name=account_name or None,
                billable=billable,
                comments=comments,
                is_active=True,
            )
        except ValidationError as exc:
            errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": exc.messages}
            return JsonResponse({"success": False, "form_errors": errors})

        account = result["account"]
        user = result["user"]
        return JsonResponse({
            "success": True,
            "account_id": account.id,
            "account_name": account.name,
            "user_id": user.id,
            "username": user.username,
            "web_account": True,
        })

    # Legacy: billing account + inactive auto user (check-in "new customer")
    composed = " ".join(
        p for p in [prefix, first_name, middle_name, last_name, suffix] if p
    ).strip()
    display = account_name or composed
    if not display:
        return JsonResponse({
            "success": False,
            "form_errors": {"first_name": ["Name is required."]},
        })

    with transaction.atomic():
        account = create_billing_account(
            actor=request.user,
            name=display,
            billable=billable,
            comments=comments,
        )
        # Inactive placeholder membership for staff edit / email tokens
        from boxes.backend.account import create_user_from_account
        user_id = create_user_from_account(account.id)
        user = CustomUser.objects.filter(pk=user_id).first() if user_id else None
        if user and phone_number:
            user.phone_number = phone_number
            user.save(update_fields=["phone_number"])
        if user and email:
            CustomUserEmail.objects.get_or_create(user=user, email=email)
            if not user.email:
                user.email = email
                user.save(update_fields=["email"])
        if user and company:
            user.company = company
            user.save(update_fields=["company"])

    return JsonResponse({
        "success": True,
        "account_id": account.id,
        "account_name": account.name,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "web_account": False,
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_user_emails(request):
    """POST (staff): update notification emails for a target user."""
    data = json.loads(request.body)
    updated_emails = dict()

    for user_id, emails in data.items():
        for key, value in emails.items():
            if key.startswith("NEW_"):
                new_email = CustomUserEmail(user_id=user_id, email=value)
                new_email.save()
                updated_emails[key] = new_email.id
            elif key.startswith("REMOVE_"):
                email_id = int(key[7:])
                email = CustomUserEmail.objects.get(id=email_id, user_id=user_id)
                email.delete()
                updated_emails[key] = True
            else:
                email = CustomUserEmail.objects.get(id=int(key), user_id=user_id)
                email.email = value
                email.save()

    return JsonResponse({"success": True, "emails": updated_emails})
