from boxes.models import *
from boxes.tasks import create_user_from_account
from django.core.paginator import Paginator
from django.db.models import Case, Exists, When, Max, F, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from html_sanitizer import Sanitizer

PACKAGES_PER_PAGE = 10

ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "code", "del", "div", "em",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "li",
    "ol", "p", "pre", "span", "strong", "sub", "sup", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "ul", "br", "u", "font"
]

# Base attributes that apply to all tags
COMMON_ATTRIBUTES = ["class", "title", "id", "style"]

# Special cases for specific tags
SPECIAL_ATTRIBUTES = {
    "a": ["href", "name", "target", "rel"],
    "img": ["src", "alt", "height", "width"],
    "font": ["color", "style"],
    "span": ["contenteditable", "style", "class"]
}

# Apply common attributes to all tags and update with special cases
ALLOWED_ATTRIBUTES = {tag: COMMON_ATTRIBUTES for tag in ALLOWED_TAGS}
ALLOWED_ATTRIBUTES.update(SPECIAL_ATTRIBUTES)


def _clean_html(html):
    sanitizer = Sanitizer({
        "tags": ALLOWED_TAGS,
        "attributes": ALLOWED_ATTRIBUTES,
        "empty": {"hr", "br"},
        "separate": {"a", "div", "p", "span"},
        "style_filter": [
            "font-family", "background-color", "color", "text-decoration",
            "font-weight", "font-style", "text-align", "height", "width"
        ]
    })
    return sanitizer.sanitize(html)


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
    ).filter(**kwargs).order_by("current_state", "-check_in_time")

    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return paginator


def _search_packages_helper(request, **kwargs):
    query = request.GET.get("q", "").strip()
    packages = _get_packages(tracking_code__icontains=query,
                             current_state=1,
                             **kwargs)

    return packages


def _get_matching_users(account_id):
    # Ensure Account exists
    account = get_object_or_404(Account.objects.select_related("accountbalance"), pk=account_id)

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
        creation_result = create_user_from_account.delay(account_id)
        return CustomUser.objects.get(pk=creation_result.get()), account
