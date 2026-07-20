"""Account-related non-HTTP helpers."""
from decimal import Decimal

from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from boxes.backend.membership import associate_user
from boxes.models import Account, AccountBalance, CustomUser, CustomUserEmail, UserAccount


CUSTOMER_GROUP_NAME = "Customer"


def ensure_customer_group(user):
    """Ensure ``user`` is in the Customer group (portal access)."""
    group, _ = Group.objects.get_or_create(name=CUSTOMER_GROUP_NAME)
    user.groups.add(group)
    return group


def ensure_account_balance(account):
    """Create zero ``AccountBalance`` row if missing."""
    balance, _ = AccountBalance.objects.get_or_create(
        account=account,
        defaults={
            "regular_balance": Decimal("0.00"),
            "late_balance": Decimal("0.00"),
        },
    )
    return balance


def _unique_random_username(length=32):
    """Return a username that does not yet exist."""
    while True:
        username = get_random_string(length)
        if not CustomUser.objects.filter(username=username).exists():
            return username


def _split_account_name(name):
    """Split a display name into first / middle / last."""
    name_parts = (name or "").split()
    if not name_parts:
        return None, None, None
    first_name = name_parts[0]
    middle_name = ""
    last_name = ""
    if len(name_parts) >= 3:
        middle_name = name_parts[1]
        last_name = " ".join(name_parts[2:])
    elif len(name_parts) == 2:
        last_name = name_parts[1]
    return first_name, middle_name, last_name


def create_user_from_account(account_id):
    """Create an inactive CustomUser linked to an account via UserAccount.

    Returns the user id when a single membership exists or a new user is
    created. Returns an existing linked user id only when there is exactly one
    membership. Returns None if the account is missing, has an empty name, or
    already has multiple linked users (ambiguous). Creates a user only when
    there are zero memberships.
    """
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return None

    existing = UserAccount.objects.filter(account=account)
    existing_count = existing.count()
    if existing_count == 1:
        return existing.first().user_id
    if existing_count > 1:
        return None

    first_name, middle_name, last_name = _split_account_name(account.name)
    if first_name is None:
        return None

    new_custom_user = CustomUser.objects.create(
        username=_unique_random_username(149),
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        is_active=False,
        date_joined=timezone.now(),
    )
    new_custom_user.set_unusable_password()
    new_custom_user.save(update_fields=["password"])
    ensure_customer_group(new_custom_user)
    associate_user(account, new_custom_user, role=UserAccount.ROLE_OWNER)
    ensure_account_balance(account)
    return new_custom_user.id


def create_billing_account(
    *,
    actor,
    name,
    billable=True,
    comments=None,
    balance=None,
    owner_user=None,
):
    """Create an Account (+ balance + primary alias), optionally owned by ``owner_user``.

    ``actor`` is stored as Account.user (creator). Returns the Account.
    """
    if not name or not str(name).strip():
        raise ValidationError({"name": ["Account name is required."]})

    account = Account.objects.create(
        user=actor,
        name=str(name).strip()[:64],
        balance=balance if balance is not None else Decimal("0.00"),
        billable=bool(billable),
        comments=(str(comments)[:256] if comments else None),
    )
    account.ensure_primary_alias()
    ensure_account_balance(account)

    if owner_user is not None:
        associate_user(account, owner_user, role=UserAccount.ROLE_OWNER, actor=actor)
        ensure_customer_group(owner_user)

    return account


def create_web_user(
    *,
    username,
    password,
    first_name,
    last_name="",
    middle_name="",
    prefix="",
    suffix="",
    company="",
    phone_number="",
    mobile_number="",
    email=None,
    is_active=True,
    account=None,
    role=UserAccount.ROLE_OWNER,
    actor=None,
):
    """Create an active portal login (Customer group) and optionally link to ``account``.

    Validates password strength and username uniqueness. Returns (user, membership|None).
    """
    username = (username or "").strip()
    if not username:
        raise ValidationError({"username": ["Username is required."]})
    if CustomUser.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": ["Username already exists."]})
    if not first_name or not str(first_name).strip():
        raise ValidationError({"first_name": ["First name is required."]})
    if not password:
        raise ValidationError({"password": ["Password is required."]})

    # Build a temporary user for validators that inspect the user object
    provisional = CustomUser(username=username, first_name=first_name, last_name=last_name or "")
    try:
        validate_password(password, user=provisional)
    except ValidationError as exc:
        raise ValidationError({"password": list(exc.messages)}) from exc

    with transaction.atomic():
        user = CustomUser.objects.create(
            username=username,
            first_name=str(first_name).strip()[:150],
            last_name=(str(last_name).strip()[:150] if last_name else ""),
            middle_name=(str(middle_name).strip()[:64] if middle_name else None),
            prefix=(str(prefix).strip()[:16] if prefix else None),
            suffix=(str(suffix).strip()[:16] if suffix else None),
            company=(str(company).strip()[:128] if company else None),
            phone_number=(str(phone_number).strip()[:20] if phone_number else None),
            mobile_number=(str(mobile_number).strip()[:20] if mobile_number else None),
            email=(str(email).strip()[:254] if email else ""),
            is_active=bool(is_active),
            date_joined=timezone.now(),
        )
        user.set_password(password)
        user.save(update_fields=["password"])
        ensure_customer_group(user)

        if email and str(email).strip():
            CustomUserEmail.objects.get_or_create(
                user=user,
                email=str(email).strip()[:254],
            )

        membership = None
        if account is not None:
            membership = associate_user(
                account,
                user,
                role=role or UserAccount.ROLE_MEMBER,
                actor=actor,
            )
            ensure_account_balance(account)

    return user, membership


def create_account_with_web_user(
    *,
    actor,
    username,
    password,
    first_name,
    last_name="",
    middle_name="",
    prefix="",
    suffix="",
    company="",
    phone_number="",
    mobile_number="",
    email=None,
    account_name=None,
    billable=True,
    comments=None,
    is_active=True,
):
    """Create a billing Account and a portal login linked as owner.

    ``account_name`` defaults to the composed person name. Returns dict with
    account, user, and membership.
    """
    composed_name = " ".join(
        part for part in [prefix, first_name, middle_name, last_name, suffix] if part
    ).strip()
    display_name = (account_name or composed_name or username).strip()[:64]

    with transaction.atomic():
        user, _ = create_web_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            prefix=prefix,
            suffix=suffix,
            company=company,
            phone_number=phone_number,
            mobile_number=mobile_number,
            email=email,
            is_active=is_active,
            account=None,
            actor=actor,
        )
        account = create_billing_account(
            actor=actor,
            name=display_name,
            billable=billable,
            comments=comments,
            owner_user=user,
        )
        membership = UserAccount.objects.get(user=user, account=account)

    return {
        "account": account,
        "user": user,
        "membership": membership,
    }


def activate_web_user(user, password=None):
    """Activate a portal user, optionally setting a new password."""
    if password:
        validate_password(password, user=user)
        user.set_password(password)
    if not user.has_usable_password() and not password:
        raise ValidationError({"password": ["Password required to activate login."]})
    user.is_active = True
    update_fields = ["is_active"]
    if password:
        update_fields.append("password")
    user.save(update_fields=update_fields)
    ensure_customer_group(user)
    return user
