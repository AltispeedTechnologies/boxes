"""Profile self-service and staff user create/update/management endpoints."""
import json

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods

from boxes.backend.account import (
    create_account_with_web_user,
    create_billing_account,
    create_web_user,
    ensure_customer_group,
)
from boxes.backend.membership import associate_user, disassociate_user
from boxes.backend.signup import (
    create_signup_invite,
    send_signup_invite_email,
)
from boxes.forms import CustomUserForm
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Account, CustomUser, CustomUserEmail, UserAccount
from boxes.models.signup import SignupInvite


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

        user = CustomUser.objects.get(pk=user_id)
        form = CustomUserForm(user_data, instance=user)
        if form.is_valid():
            form.save()
        else:
            return JsonResponse({"success": False, "form_errors": form.errors})

    return JsonResponse({"success": True})


def _unique_random_username(length=32):
    while True:
        username = get_random_string(length)
        if not CustomUser.objects.filter(username=username).exists():
            return username


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ("1", "true", "yes", "on")


@require_http_methods(["POST"])
@exception_catcher()
def create_user(request):
    """POST (staff): create user and/or billing account, or send a signup invite.

    Body JSON supports several modes:

    **Invite (preferred self-registration)**
      - send_invite=true, email required
      - create_account (bool, default false): also create a billing Account to
        link when the invitee registers
      - optional name/company/phone fields prefill the invite

    **Web user without account**
      - create_account=false, username+password (or create_web_account=true)
      - creates an active Customer-group login with no billing Account

    **Account + optional web login** (legacy / check-in "new customer")
      - create_account=true (default when send_invite is false)
      - with username+password or create_web_account: active portal login
      - without credentials: inactive placeholder membership user
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
    create_web = _as_bool(data.get("create_web_account") or data.get("web_account"))
    send_invite = _as_bool(data.get("send_invite") or data.get("invite"))
    # Default create_account=True for legacy paths; False when only inviting a login
    if "create_account" in data or "create_billing_account" in data:
        create_account = _as_bool(
            data.get("create_account", data.get("create_billing_account")),
            default=True,
        )
    else:
        # Invites default to no billing account; credential creates without
        # explicit flag still default to account for check-in modal compat
        create_account = not send_invite
    billable = _as_bool(data.get("billable"), default=True)
    comments = data.get("comments")
    account_name = (data.get("account_name") or data.get("name") or "").strip()
    account_id = data.get("account_id")
    role = (data.get("role") or UserAccount.ROLE_OWNER).strip()

    if password2 is not None and password and password != password2:
        return JsonResponse({
            "success": False,
            "form_errors": {"password": ["Passwords do not match."]},
        })

    # ---- Invite path: no user created until customer accepts the link ----
    if send_invite:
        if not email:
            return JsonResponse({
                "success": False,
                "form_errors": {"email": ["Email is required to send a sign-up invitation."]},
            })
        linked_account = None
        if account_id:
            linked_account = get_object_or_404(Account, pk=account_id)
            # If linking an existing account, do not also create a new one
            create_account = False

        try:
            invite = create_signup_invite(
                email=email,
                actor=request.user,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                prefix=prefix,
                suffix=suffix,
                company=company,
                phone_number=phone_number,
                mobile_number=mobile_number,
                account=linked_account,
                role=role,
                create_account=create_account,
                account_name=account_name or None,
                billable=billable,
                comments=comments,
            )
        except ValidationError as exc:
            errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": list(exc.messages)}
            return JsonResponse({"success": False, "form_errors": errors})

        email_sent = send_signup_invite_email(invite, request=request)
        return JsonResponse({
            "success": True,
            "invite": True,
            "invite_id": invite.id,
            "email": invite.email,
            "email_sent": email_sent,
            "signup_path": f"/signup/{invite.token}/",
            "account_id": invite.account_id,
            "account_name": invite.account.name if invite.account_id else None,
            "web_account": False,
            "message": (
                "Sign-up invitation sent."
                if email_sent
                else "Invitation created, but the email could not be sent. "
                     "Share the sign-up link manually."
            ),
            "last_error": invite.last_error or "",
        })

    wants_web = create_web or (username and password)
    if create_web and (not username or not password):
        return JsonResponse({
            "success": False,
            "form_errors": {
                "username": ["Username is required for web accounts."] if not username else [],
                "password": ["Password is required for web accounts."] if not password else [],
            },
        })

    if not first_name and not account_name and not (wants_web and username):
        return JsonResponse({
            "success": False,
            "form_errors": {"first_name": ["First name is required."]},
        })

    # ---- User only (no billing account) ----
    if wants_web and not create_account:
        try:
            user, membership = create_web_user(
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
                is_active=True,
                account=None,
                actor=request.user,
            )
        except ValidationError as exc:
            errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": list(exc.messages)}
            return JsonResponse({"success": False, "form_errors": errors})

        return JsonResponse({
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "account_id": None,
            "account_name": None,
            "web_account": True,
            "create_account": False,
        })

    # ---- Account + web login ----
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
            errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": list(exc.messages)}
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
            "create_account": True,
        })

    # ---- Legacy: billing account + inactive auto user (check-in "new customer") ----
    if not create_account:
        return JsonResponse({
            "success": False,
            "form_errors": {
                "__all__": [
                    "Provide username/password to create a user without an account, "
                    "or set create_account true to create a billing account."
                ]
            },
        })

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
        "create_account": True,
    })


@require_http_methods(["GET"])
def user_mgmt(request):
    """GET (staff): list/search portal and staff users independently of accounts."""
    query = (request.GET.get("q") or "").strip()
    filter_mode = (request.GET.get("filter") or "all").strip().lower()

    users = CustomUser.objects.annotate(
        active_account_count=Count(
            "account_memberships",
            filter=Q(account_memberships__is_active=True),
            distinct=True,
        ),
        account_count=Count("account_memberships", distinct=True),
    ).order_by("username")

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(company__icontains=query)
            | Q(customuseremail__email__icontains=query)
        ).distinct()

    if filter_mode == "no_account":
        users = users.filter(active_account_count=0)
    elif filter_mode == "inactive":
        users = users.filter(is_active=False)
    elif filter_mode == "active":
        users = users.filter(is_active=True)
    elif filter_mode == "staff":
        users = users.filter(groups__name="Staff").distinct()
    elif filter_mode == "customer":
        users = users.filter(groups__name="Customer").distinct()

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 25)
    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page_number)

    pending_invites = SignupInvite.objects.filter(used_at__isnull=True).count()

    return render(request, "mgmt/users.html", {
        "page_obj": page_obj,
        "query": query,
        "filter_mode": filter_mode,
        "pending_invites": pending_invites,
    })


@require_http_methods(["GET"])
def user_detail(request, pk):
    """GET (staff): user detail / edit page (login identity, not billing account)."""
    user = get_object_or_404(CustomUser, pk=pk)
    emails = CustomUserEmail.objects.filter(user=user).order_by("id")
    memberships = (
        UserAccount.objects.filter(user=user)
        .select_related("account")
        .order_by("-is_active", "role", "account__name")
    )
    groups = list(user.groups.values_list("name", flat=True))
    all_groups = list(Group.objects.order_by("name").values_list("name", flat=True))
    invites = SignupInvite.objects.filter(
        Q(email__iexact=user.email) | Q(used_by=user)
    ).order_by("-created_at")[:10] if user.email else SignupInvite.objects.filter(
        used_by=user
    ).order_by("-created_at")[:10]

    return render(request, "mgmt/user_edit.html", {
        "custom_user": user,
        "emails": emails,
        "memberships": memberships,
        "groups": groups,
        "all_groups": all_groups,
        "invites": invites,
    })


@require_http_methods(["POST"])
@exception_catcher()
def update_user_status(request, pk):
    """POST (staff): activate/deactivate user and optional password / groups."""
    user = get_object_or_404(CustomUser, pk=pk)
    data = json.loads(request.body) if request.body else {}

    with transaction.atomic():
        if "is_active" in data:
            user.is_active = _as_bool(data.get("is_active"))
            user.save(update_fields=["is_active"])

        password = data.get("password") or data.get("password1") or ""
        password2 = data.get("password2")
        if password:
            if password2 is not None and password != password2:
                return JsonResponse({
                    "success": False,
                    "form_errors": {"password": ["Passwords do not match."]},
                })
            try:
                validate_password(password, user=user)
            except ValidationError as exc:
                return JsonResponse({
                    "success": False,
                    "form_errors": {"password": list(exc.messages)},
                })
            user.set_password(password)
            user.save(update_fields=["password"])

        if "groups" in data:
            group_names = data.get("groups") or []
            if not isinstance(group_names, list):
                group_names = [group_names]
            groups = list(Group.objects.filter(name__in=group_names))
            user.groups.set(groups)

    return JsonResponse({
        "success": True,
        "user_id": user.id,
        "is_active": user.is_active,
        "groups": list(user.groups.values_list("name", flat=True)),
    })


@require_http_methods(["POST"])
@exception_catcher()
def user_link_account(request, pk):
    """POST (staff): link this user to a billing account by account_id."""
    user = get_object_or_404(CustomUser, pk=pk)
    data = json.loads(request.body) if request.body else {}
    account_id = data.get("account_id")
    if not account_id:
        return JsonResponse({
            "success": False,
            "form_errors": {"account_id": ["Account is required."]},
        })
    account = get_object_or_404(Account, pk=account_id)
    role = data.get("role") or UserAccount.ROLE_MEMBER
    try:
        membership = associate_user(account, user, role=role, actor=request.user)
        ensure_customer_group(user)
    except ValidationError as exc:
        return JsonResponse({"success": False, "errors": list(exc.messages)}, status=400)

    return JsonResponse({
        "success": True,
        "membership": {
            "id": membership.id,
            "user_id": membership.user_id,
            "account_id": membership.account_id,
            "role": membership.role,
            "is_active": membership.is_active,
            "account_name": account.name,
        },
    })


@require_http_methods(["POST"])
@exception_catcher()
def user_unlink_account(request, pk):
    """POST (staff): soft-disassociate this user from a billing account."""
    user = get_object_or_404(CustomUser, pk=pk)
    data = json.loads(request.body) if request.body else {}
    account_id = data.get("account_id")
    if not account_id:
        return JsonResponse({
            "success": False,
            "form_errors": {"account_id": ["Account is required."]},
        })
    account = get_object_or_404(Account, pk=account_id)
    allow_last = _as_bool(data.get("allow_last_owner"))
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
def send_user_invite(request, pk=None):
    """POST (staff): create/send a signup invite (optionally for an existing email).

    When ``pk`` is provided, prefills from that user (does not replace them).
    Body may also stand alone with email + name fields.
    """
    data = json.loads(request.body) if request.body else {}
    source_user = None
    if pk is not None:
        source_user = get_object_or_404(CustomUser, pk=pk)

    email = (data.get("email") or (source_user.email if source_user else "") or "").strip()
    if not email and source_user:
        first_extra = CustomUserEmail.objects.filter(user=source_user).order_by("id").first()
        if first_extra:
            email = first_extra.email

    if not email:
        return JsonResponse({
            "success": False,
            "form_errors": {"email": ["Email is required to send a sign-up invitation."]},
        })

    account_id = data.get("account_id")
    account = get_object_or_404(Account, pk=account_id) if account_id else None
    create_account = _as_bool(data.get("create_account"), default=False)

    try:
        invite = create_signup_invite(
            email=email,
            actor=request.user,
            first_name=(data.get("first_name") or (source_user.first_name if source_user else "") or ""),
            last_name=(data.get("last_name") or (source_user.last_name if source_user else "") or ""),
            company=(data.get("company") or (source_user.company if source_user else "") or ""),
            phone_number=(data.get("phone_number") or (source_user.phone_number if source_user else "") or ""),
            account=account,
            role=data.get("role") or UserAccount.ROLE_OWNER,
            create_account=create_account and account is None,
            account_name=(data.get("account_name") or "").strip() or None,
        )
    except ValidationError as exc:
        errors = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": list(exc.messages)}
        return JsonResponse({"success": False, "form_errors": errors})

    email_sent = send_signup_invite_email(invite, request=request)
    return JsonResponse({
        "success": True,
        "invite_id": invite.id,
        "email": invite.email,
        "email_sent": email_sent,
        "signup_path": f"/signup/{invite.token}/",
        "account_id": invite.account_id,
        "last_error": invite.last_error or "",
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
