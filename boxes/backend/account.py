from boxes.models import Account, CustomUser, UserAccount
from django.utils import timezone
from django.utils.crypto import get_random_string


def create_user_from_account(account_id):
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return None, None

    # If no UserAccount entry exists, create a CustomUser
    # Split the account.name into name parts
    name_parts = account.name.split(" ")

    # If the account name is empty, do nothing
    if len(name_parts) == 0:
        return None, account

    first_name, middle_name, last_name = name_parts[0], "", ""

    if len(name_parts) >= 3:
        middle_name = name_parts[1]
        last_name = " ".join(name_parts[2:])
    elif len(name_parts) == 2:
        middle_name = ""
        last_name = name_parts[1]

    # Create a CustomUser with a useless password and login disabled
    new_custom_user = CustomUser.objects.create(
        username=account.name[:150],
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        is_active=False,
        password=get_random_string(128),
        date_joined=timezone.now()
    )
    # Create a UserAccount with the new CustomUser
    UserAccount.objects.create(user=new_custom_user, account=account)
    # Return the new CustomUser object
    return new_custom_user.id
