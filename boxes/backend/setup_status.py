"""Management setup completeness: what staff must configure for a usable install.

Used by the navbar Management dropdown (warning icons), mgmt page banners, and
``GET /mgmt/setup-status`` for robust client-side refresh after saves.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.urls import NoReverseMatch, reverse

CACHE_KEY = "boxes_mgmt_setup_status_v1"
CACHE_TTL_SECONDS = 45

# GlobalSettings.load() default name — treat as unconfigured branding
_DEFAULT_BUSINESS_NAME = "Boxes"


@dataclass
class SetupItem:
    """One Management menu entry's configuration status."""

    key: str
    label: str
    url_name: str
    required: bool
    ok: bool
    issues: list[str] = field(default_factory=list)
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def invalidate_setup_status_cache() -> None:
    """Drop cached setup status (call after any mgmt settings save)."""
    cache.delete(CACHE_KEY)


def _url(name: str) -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""



def _check_general() -> SetupItem:
    from boxes.models import GlobalSettings

    gs = GlobalSettings.load()
    hard: list[str] = []
    soft: list[str] = []
    name = (gs.name or "").strip()
    if not name:
        hard.append("Set your business name (General).")
    elif name == _DEFAULT_BUSINESS_NAME and not (gs.address1 or "").strip():
        hard.append("Set your business name and address (still using defaults).")
    if not (gs.address1 or "").strip():
        hard.append("Set business address (used on labels and invoices).")
    if not (gs.email or "").strip() and not (gs.phone_number or "").strip():
        hard.append("Set a business email or phone number for customer contact on labels.")
    if not gs.login_image and not gs.source_image:
        soft.append("Upload a logo (recommended for login and labels).")

    issues = hard + soft
    return SetupItem(
        key="general",
        label="General",
        url_name="general_settings",
        required=True,
        ok=len(issues) == 0,
        issues=issues,
        url=_url("general_settings"),
    )




def _check_carriers() -> SetupItem:
    from boxes.models import Carrier

    qs = Carrier.objects.filter(is_active=True)
    count = qs.count()
    issues = []
    if count < 1:
        issues.append("Add at least one active carrier for package check-in.")
    return SetupItem(
        key="carriers",
        label="Carriers",
        url_name="carrier_settings",
        required=True,
        ok=count >= 1,
        issues=issues,
        url=_url("carrier_settings"),
    )


def _check_package_types() -> SetupItem:
    from boxes.models import PackageType

    count = PackageType.objects.filter(is_active=True).count()
    issues = []
    if count < 1:
        issues.append("Add at least one active package type with a default price.")
    return SetupItem(
        key="package_types",
        label="Package Types",
        url_name="package_type_settings",
        required=True,
        ok=count >= 1,
        issues=issues,
        url=_url("package_type_settings"),
    )


def _check_charges() -> SetupItem:
    from boxes.models import AccountChargeSettings

    count = AccountChargeSettings.objects.count()
    issues = []
    # Not required for bare check-in, but needed for automatic storage/aging fees
    if count < 1:
        issues.append(
            "No charge rules configured. Storage and late fees will not age automatically."
        )
    return SetupItem(
        key="charges",
        label="Charges",
        url_name="charge_settings",
        required=False,
        ok=count >= 1,
        issues=issues,
        url=_url("charge_settings"),
    )


def _check_emails() -> SetupItem:
    from boxes.models import EmailSettings, EmailTemplate, GlobalSettings

    gs = GlobalSettings.load()
    issues = []
    es = EmailSettings.objects.order_by("pk").first()

    if not gs.email_sending:
        # Explicitly off — treat as configured (no outbound expected)
        return SetupItem(
            key="emails",
            label="Emails",
            url_name="email_settings",
            required=False,
            ok=True,
            issues=[],
            url=_url("email_settings"),
        )

    if es is None:
        issues.append("Create email sender settings (name and from address).")
    else:
        if not (es.sender_name or "").strip():
            issues.append("Set email sender name.")
        if not (es.sender_email or "").strip():
            issues.append("Set email sender address.")
        if es.check_in_template_id is None:
            issues.append("Choose a default check-in email template.")

    template_count = EmailTemplate.objects.count()
    if template_count < 1:
        issues.append("Create at least one email template.")

    public = getattr(settings, "MJ_APIKEY_PUBLIC", None)
    private = getattr(settings, "MJ_APIKEY_PRIVATE", None)
    if not public or not private:
        issues.append("Mailjet API keys are not set in the environment (needed to send mail).")

    return SetupItem(
        key="emails",
        label="Emails",
        url_name="email_settings",
        required=False,  # warehouse can run without email
        ok=len(issues) == 0,
        issues=issues,
        url=_url("email_settings"),
    )


def _check_email_templates() -> SetupItem:
    from boxes.models import EmailTemplate, GlobalSettings

    gs = GlobalSettings.load()
    count = EmailTemplate.objects.count()
    issues = []
    if count < 1:
        issues.append("Create at least one email template for notifications and invites.")
    # Required only when email sending is on
    required = bool(gs.email_sending)
    return SetupItem(
        key="email_templates",
        label="Email Templates",
        url_name="email_template",
        required=required,
        ok=count >= 1,
        issues=issues if count < 1 else [],
        url=_url("email_template"),
    )


def _check_pickup() -> SetupItem:
    from datetime import date, timedelta

    from boxes.models import PickupDay, PickupScheduleRule

    rules = PickupScheduleRule.objects.count()
    today = date.today()
    open_days = PickupDay.objects.filter(
        date__gte=today, date__lte=today + timedelta(days=30), is_active=True
    ).count()
    issues = []
    if rules < 1 and open_days < 1:
        issues.append(
            "No pickup schedule rules or open pickup days. Customer reservation needs at least one open day."
        )
    return SetupItem(
        key="pickup",
        label="Pickup Days",
        url_name="pickup_mgmt",
        required=False,
        ok=rules >= 1 or open_days >= 1,
        issues=issues,
        url=_url("pickup_mgmt"),
    )


def _check_stripe() -> SetupItem:
    key = getattr(settings, "STRIPE_API_KEY", None)
    issues = []
    if not key:
        issues.append("STRIPE_API_KEY is not set. Customer card payments will not work.")
    return SetupItem(
        key="stripe",
        label="Stripe Totals",
        url_name="stripe_totals",
        required=False,
        ok=bool(key),
        issues=issues,
        url=_url("stripe_totals"),
    )


def compute_setup_status(*, use_cache: bool = True) -> dict[str, Any]:
    """Return full setup status dict for navbar and API.

    Structure::

        {
          "items": { key: SetupItem dict, ... },
          "order": [key, ...],  # Management menu order
          "required_incomplete": bool,
          "any_incomplete": bool,
          "required_issues": [str, ...],
          "all_issues": [str, ...],
        }
    """
    if use_cache:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached

    # Order matches Management dropdown (operational first, then config)
    builders = [
        ("accounts", None),  # operational — never warn for "setup"
        ("users", None),
        ("stripe", _check_stripe),
        ("carriers", _check_carriers),
        ("charges", _check_charges),
        ("emails", _check_emails),
        ("email_templates", _check_email_templates),
        ("general", _check_general),
        ("package_types", _check_package_types),
        ("pickup", _check_pickup),
    ]

    items: dict[str, dict] = {}
    order: list[str] = []

    # Operational entries always ok (no setup flag)
    items["accounts"] = SetupItem(
        key="accounts",
        label="Accounts and Users",
        url_name="account_mgmt",
        required=False,
        ok=True,
        issues=[],
        url=_url("account_mgmt"),
    ).to_dict()
    order.append("accounts")

    items["users"] = SetupItem(
        key="users",
        label="Users",
        url_name="user_mgmt",
        required=False,
        ok=True,
        issues=[],
        url=_url("user_mgmt"),
    ).to_dict()
    order.append("users")

    for key, builder in builders:
        if builder is None:
            continue
        item = builder()
        item.url = item.url or _url(item.url_name)
        items[item.key] = item.to_dict()
        order.append(item.key)

    required_issues = []
    all_issues = []
    required_incomplete = False
    any_incomplete = False
    for key in order:
        it = items[key]
        if not it["ok"]:
            any_incomplete = True
            all_issues.extend(it["issues"])
            if it["required"]:
                required_incomplete = True
                required_issues.extend(it["issues"])

    result = {
        "items": items,
        "order": order,
        "required_incomplete": required_incomplete,
        "any_incomplete": any_incomplete,
        "required_issues": required_issues,
        "all_issues": all_issues,
    }
    cache.set(CACHE_KEY, result, CACHE_TTL_SECONDS)
    return result


def setup_status_for_template() -> dict[str, Any]:
    """Lightweight dict for templates (navbar)."""
    return compute_setup_status(use_cache=True)
