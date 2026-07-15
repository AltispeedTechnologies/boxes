"""Account-related non-HTTP helpers."""
from boxes.backend.membership import associate_user
from boxes.models import Account, CustomUser, UserAccount
from django.utils import timezone
from django.utils.crypto import get_random_string


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

    # Split the account.name into name parts
    name_parts = account.name.split()

    # If the account name is empty, do nothing
    if not name_parts:
        return None

    first_name, middle_name, last_name = name_parts[0], "", ""

    if len(name_parts) >= 3:
        middle_name = name_parts[1]
        last_name = " ".join(name_parts[2:])
    elif len(name_parts) == 2:
        middle_name = ""
        last_name = name_parts[1]

    # Create a CustomUser with a useless password and login disabled
    # Use a unique random username; account names are not guaranteed unique
    while True:
        username = get_random_string(149)
        if not CustomUser.objects.filter(username=username).exists():
            break

    new_custom_user = CustomUser.objects.create(
        username=username,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        is_active=False,
        password=get_random_string(128),
        date_joined=timezone.now()
    )
    associate_user(account, new_custom_user, role=UserAccount.ROLE_OWNER)
    return new_custom_user.id
