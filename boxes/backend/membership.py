"""CustomUser ↔ Account membership helpers (portal multi-account support)."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404

from boxes.models import Account, CustomUser, UserAccount

ACTIVE_ACCOUNT_SESSION_KEY = "active_account_id"
VALID_ROLES = {UserAccount.ROLE_OWNER, UserAccount.ROLE_MEMBER}


def list_accounts_for_user(user, active_only=True):
    """Return accounts linked to ``user`` ordered by name."""
    qs = Account.objects.filter(user_memberships__user=user)
    if active_only:
        qs = qs.filter(user_memberships__is_active=True)
    return qs.distinct().order_by("name")


def list_users_for_account(account, active_only=True):
    """Return users linked to ``account`` ordered by username."""
    qs = CustomUser.objects.filter(account_memberships__account=account)
    if active_only:
        qs = qs.filter(account_memberships__is_active=True)
    return qs.distinct().order_by("username")


def get_membership(user, account, active_only=True):
    """Return UserAccount row for user+account, or None."""
    qs = UserAccount.objects.filter(user=user, account=account)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.first()


def get_active_account(request):
    """Resolve the request user active Account from session / memberships.

    Session key: ``active_account_id``. If missing/invalid and the user has
    exactly one active membership, that account is returned. If the user has
    multiple active memberships and no valid session selection, returns None.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None

    memberships = UserAccount.objects.filter(user=user, is_active=True).select_related("account")
    count = memberships.count()
    if count == 0:
        return None

    session_account_id = request.session.get(ACTIVE_ACCOUNT_SESSION_KEY)
    if session_account_id is not None:
        try:
            session_account_id = int(session_account_id)
        except (TypeError, ValueError):
            session_account_id = None
        if session_account_id is not None:
            match = memberships.filter(account_id=session_account_id).first()
            if match:
                return match.account

    if count == 1:
        return memberships.first().account

    return None


def set_active_account(request, account_id):
    """Set session active account after validating active membership.

    Returns the Account. Raises PermissionDenied if the user is not an active member.
    """
    user = request.user
    account = get_object_or_404(Account, pk=account_id)
    require_account_member(user, account)
    request.session[ACTIVE_ACCOUNT_SESSION_KEY] = int(account.id)
    return account


def clear_active_account_if_matches(request, account_id):
    """Drop session active account when it matches ``account_id``."""
    try:
        current = request.session.get(ACTIVE_ACCOUNT_SESSION_KEY)
        if current is not None and int(current) == int(account_id):
            del request.session[ACTIVE_ACCOUNT_SESSION_KEY]
    except (TypeError, ValueError, KeyError):
        pass


def associate_user(account, user, role=UserAccount.ROLE_MEMBER, actor=None):
    """Link ``user`` to ``account`` idempotently; reactivate if soft-disabled.

    ``actor`` is reserved for future audit logging.
    """
    del actor  # reserved
    if role not in VALID_ROLES:
        raise ValidationError({"role": [f"Invalid role {role!r}."]})

    membership, created = UserAccount.objects.get_or_create(
        user=user,
        account=account,
        defaults={
            "role": role or UserAccount.ROLE_MEMBER,
            "is_active": True,
        },
    )
    if not created:
        changed = False
        if not membership.is_active:
            membership.is_active = True
            changed = True
        if role and membership.role != role:
            membership.role = role
            changed = True
        if changed:
            membership.save()
    return membership


def disassociate_user(account, user, actor=None, *, allow_last_owner=False):
    """Soft-disable membership (``is_active=False``). No-op if missing.

    Refuses to deactivate the last active owner unless ``allow_last_owner``.
    ``actor`` is reserved for future audit logging. Returns the membership or None.
    """
    del actor  # reserved
    membership = UserAccount.objects.filter(user=user, account=account).first()
    if membership is None:
        return None

    if membership.is_active and membership.role == UserAccount.ROLE_OWNER and not allow_last_owner:
        other_owners = UserAccount.objects.filter(
            account=account,
            role=UserAccount.ROLE_OWNER,
            is_active=True,
        ).exclude(pk=membership.pk).exists()
        if not other_owners:
            raise ValidationError(
                "Cannot disassociate the last active owner. "
                "Promote another member to owner first, or pass allow_last_owner."
            )

    if membership.is_active:
        membership.is_active = False
        membership.save(update_fields=["is_active"])
    return membership


def require_account_member(user, account):
    """Raise PermissionDenied unless ``user`` has an active membership on ``account``."""
    exists = UserAccount.objects.filter(
        user=user,
        account=account,
        is_active=True,
    ).exists()
    if not exists:
        raise PermissionDenied("Not an active member of this account.")


def search_users(term, limit=20):
    """Staff helper: find CustomUsers by username, name, or email (case-insensitive)."""
    term = (term or "").strip()
    qs = CustomUser.objects.all().order_by("username")
    if term:
        qs = qs.filter(
            Q(username__icontains=term)
            | Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(email__icontains=term)
            | Q(company__icontains=term)
        )
    return qs[:limit]
