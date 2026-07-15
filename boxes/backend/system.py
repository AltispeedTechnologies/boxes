"""Helpers for automated actors and singleton configuration rows."""
from boxes.models import CustomUser


SYSTEM_USERNAME = "system"


def get_system_user():
    """Return the CustomUser used for automated ledger and system actions.

    Prefers an inactive user named ``system``. Falls back to the earliest
    superuser, then the earliest user by primary key. Creates the system
    user when the database has no users yet (migrations / empty installs).
    """
    user = CustomUser.objects.filter(username=SYSTEM_USERNAME).first()
    if user:
        return user

    user = CustomUser.objects.filter(is_superuser=True).order_by("pk").first()
    if user:
        return user

    user = CustomUser.objects.order_by("pk").first()
    if user:
        return user

    return CustomUser.objects.create_user(
        username=SYSTEM_USERNAME,
        password=CustomUser.objects.make_random_password(length=64),
        is_active=False,
        is_staff=False,
    )


def get_system_user_pk():
    """Primary key of the system user (for on_delete=SET callables)."""
    return get_system_user().pk


def ensure_system_user():
    """Create the inactive ``system`` user if it does not exist yet."""
    user, created = CustomUser.objects.get_or_create(
        username=SYSTEM_USERNAME,
        defaults={
            "is_active": False,
            "is_staff": False,
            "first_name": "System",
            "last_name": "User",
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user
