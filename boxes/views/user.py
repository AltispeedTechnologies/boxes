import json
from boxes.forms import CustomUserForm
from boxes.models import Account, CustomUser, CustomUserEmail, UserAccount
from boxes.management.exception_catcher import exception_catcher
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.utils.crypto import get_random_string


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
        Account.objects.filter(useraccount__user=user)
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
        UserAccount.objects.filter(user=user).values_list("account_id", flat=True)
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
    data = json.loads(request.body)

    responses = {}
    for user_id, user_data in data.items():
        accounts = UserAccount.objects.filter(user=user_id).values_list("account_id", flat=True)
        if len(accounts) == 1:
            new_account_name = ""

            for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"]:
                new_account_name += user_data[field] + " " if len(user_data[field]) > 0 else ""

            account = Account.objects.filter(pk=accounts[0]).first()
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


# Generate a unique username
def generate_username():
    while True:
        username = get_random_string(149)
        if not CustomUser.objects.filter(username=username).exists():
            return username


@require_http_methods(["POST"])
@exception_catcher()
def create_user(request):
    data = json.loads(request.body)
    data["username"] = generate_username()

    with transaction.atomic():
        form = CustomUserForm(data)

        if form.is_valid():
            user = form.save()
            new_account_name = " ".join(
                data.get(field, "") for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"]
                if data.get(field)
            ).strip()

            account = Account(user=user, name=new_account_name, balance=0.00, billable=True)
            account.save()
            account.ensure_primary_alias()

            UserAccount.objects.create(user=user, account=account)

            return JsonResponse({"success": True, "account_id": account.id, "account_name": new_account_name})
        else:
            return JsonResponse({"success": False, "form_errors": form.errors})


@require_http_methods(["POST"])
@exception_catcher()
def update_user_emails(request):
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
