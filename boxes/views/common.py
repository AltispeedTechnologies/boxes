from boxes.models import *
from django.core.paginator import Paginator
from django.db.models import Case, Exists, When, Max, F, OuterRef
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils import timezone

PACKAGES_PER_PAGE = 10

def _get_packages(**kwargs):
    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related(
        "account", "carrier", "packagetype", "packagepicklist"
    ).annotate(
        check_in_time=Max(Case(
            When(packageledger__state=1, then="packageledger__timestamp")
        )),
        check_out_time=Max(Case(
            When(packageledger__state=2, then="packageledger__timestamp")
        )),
        picklist_id=F("packagepicklist__picklist_id")
    ).values(
        "id",
        "picklist_id",
        "account_id",
        "carrier_id",
        "package_type_id",
        "current_state",
        "inside",
        "price",
        "carrier__name",
        "account__name",
        "package_type__description",
        "tracking_code",
        "comments",
        "check_in_time",
        "check_out_time"
    ).filter(**kwargs
    ).order_by("current_state", "-check_in_time")

    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return paginator

def _search_packages_helper(request, **kwargs):
    query = request.GET.get("q", "").strip()
    packages = _get_packages(tracking_code__icontains=query,
                             current_state__in=[1,2],
                             **kwargs)
    
    return packages

def _get_matching_users(account_id):
    # Ensure Account exists
    account = get_object_or_404(Account, pk=account_id)
    
    # Check if there is a UserAccount entry for this account id
    user_accounts = UserAccount.objects.filter(account=account)
    
    if user_accounts.exists():
        # Check if the relationship is one-to-one
        if user_accounts.count() == 1:
            custom_user = user_accounts.first().user
            return custom_user, account
        else:
            # There are multiple CustomUser objects for this Account
            custom_users = [user_account.user for user_account in user_accounts]
            # Return all CustomUser objects that match the account
            return custom_users, account
    else:
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
        return new_custom_user, account
