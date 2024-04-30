from boxes.models import *
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils import timezone

PACKAGES_PER_PAGE = 10

def _get_packages(**kwargs):
    check_in_subquery = PackageLedger.objects.filter(
        package_id=OuterRef("pk"),
        state=1
    ).order_by("-timestamp").values("timestamp")[:1]

    check_out_subquery = PackageLedger.objects.filter(
        package_id=OuterRef("pk"),
        state=2
    ).order_by("-timestamp").values("timestamp")[:1]

    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related(
        "account", "carrier", "packagetype", "packagepicklist"
    ).annotate(
        check_in_time=Subquery(check_in_subquery),
        check_out_time=Subquery(check_out_subquery),
        custom_order=Case(
            When(current_state=1, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).values(
        "id",
        "packagepicklist__picklist_id",
        "account_id",
        "carrier_id",
        "package_type_id",
        "current_state",
        "price",
        "carrier__name",
        "account__name",
        "package_type__description",
        "tracking_code",
        "comments",
        "check_in_time",
        "check_out_time"
    ).filter(**kwargs
    ).order_by("custom_order", "current_state")

    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return paginator

def _search_packages_helper(request, **kwargs):
    query = request.GET.get("q", "").strip()
    packages = _get_packages(tracking_code__icontains=query, **kwargs)
    
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
        
        # Determine how to assign the name parts
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = name_parts[1] if len(name_parts) == 3 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
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
