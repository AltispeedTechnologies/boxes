"""Management setup completeness: DB settings and /etc/boxes.env API keys.

Used by the navbar Management dropdown (warning icons), mgmt page banners, and
``GET /mgmt/setup-status`` for robust client-side refresh after saves.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.urls import NoReverseMatch, reverse

CACHE_KEY = "boxes_mgmt_setup_status_v2"
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
        return asdict(self)


def invalidate_setup_status_cache() -> None:
    """Drop cached setup status (call after any mgmt settings save)."""
    cache.delete(CACHE_KEY)
    # Also drop previous key version if present
    cache.delete("boxes_mgmt_setup_status_v1")


def _url(name: str) -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def _truthy_str(value) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s or s.lower() in ("none", "null", "undefined", "changeme", "your-key-here"):
        return False
    return True


def env_api_key_status() -> dict[str, Any]:
    """Inspect Django settings loaded from /etc/boxes.env for integration keys.

    Does **not** return secret values — only presence and basic format checks.
    """
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str, required_for: str):
        checks.append({
            "name": name,
            "ok": ok,
            "detail": detail,
            "required_for": required_for,
        })

    # Mailjet
    mj_pub = getattr(settings, "MJ_APIKEY_PUBLIC", None)
    mj_priv = getattr(settings, "MJ_APIKEY_PRIVATE", None)
    if not _truthy_str(mj_pub):
        add("MJ_APIKEY_PUBLIC", False, "Not set in /etc/boxes.env", "Outbound email (Mailjet)")
    elif len(str(mj_pub).strip()) < 16:
        add("MJ_APIKEY_PUBLIC", False, "Value looks too short to be a real API key", "Outbound email (Mailjet)")
    else:
        add("MJ_APIKEY_PUBLIC", True, "Set", "Outbound email (Mailjet)")

    if not _truthy_str(mj_priv):
        add("MJ_APIKEY_PRIVATE", False, "Not set in /etc/boxes.env", "Outbound email (Mailjet)")
    elif len(str(mj_priv).strip()) < 16:
        add("MJ_APIKEY_PRIVATE", False, "Value looks too short to be a real API key", "Outbound email (Mailjet)")
    else:
        add("MJ_APIKEY_PRIVATE", True, "Set", "Outbound email (Mailjet)")

    # Stripe
    stripe_key = getattr(settings, "STRIPE_API_KEY", None)
    if not _truthy_str(stripe_key):
        add("STRIPE_API_KEY", False, "Not set in /etc/boxes.env", "Customer card payments")
    else:
        sk = str(stripe_key).strip()
        if not (sk.startswith("sk_") or sk.startswith("rk_")):
            add(
                "STRIPE_API_KEY",
                False,
                "Does not look like a Stripe secret key (expected sk_… or rk_…)",
                "Customer card payments",
            )
        else:
            add("STRIPE_API_KEY", True, "Set (format looks valid)", "Customer card payments")

    stripe_wh = getattr(settings, "STRIPE_ENDPOINT_SECRET", None)
    if not _truthy_str(stripe_wh):
        add(
            "STRIPE_ENDPOINT_SECRET",
            False,
            "Not set in /etc/boxes.env",
            "Stripe webhooks (payment confirmation)",
        )
    else:
        wh = str(stripe_wh).strip()
        if not wh.startswith("whsec_"):
            add(
                "STRIPE_ENDPOINT_SECRET",
                False,
                "Does not look like a Stripe webhook secret (expected whsec_…)",
                "Stripe webhooks (payment confirmation)",
            )
        else:
            add("STRIPE_ENDPOINT_SECRET", True, "Set (format looks valid)", "Stripe webhooks")

    # Optional Mailjet webhook auth
    mj_wh_secret = getattr(settings, "MAILJET_WEBHOOK_SECRET", None)
    mj_wh_user = getattr(settings, "MAILJET_WEBHOOK_USER", None)
    mj_wh_pass = getattr(settings, "MAILJET_WEBHOOK_PASSWORD", None)
    if _truthy_str(mj_wh_secret) or (_truthy_str(mj_wh_user) and _truthy_str(mj_wh_pass)):
        add(
            "MAILJET_WEBHOOK_AUTH",
            True,
            "Webhook auth configured",
            "Mailjet delivery webhooks",
        )
    else:
        add(
            "MAILJET_WEBHOOK_AUTH",
            False,
            "MAILJET_WEBHOOK_SECRET or USER/PASSWORD not set (webhooks may be open or rejected)",
            "Mailjet delivery webhooks",
        )

    missing = [c for c in checks if not c["ok"]]
    # Hard failures for payments/email (not optional webhook auth alone)
    hard_names = {
        "MJ_APIKEY_PUBLIC",
        "MJ_APIKEY_PRIVATE",
        "STRIPE_API_KEY",
        "STRIPE_ENDPOINT_SECRET",
    }
    hard_missing = [c for c in missing if c["name"] in hard_names]

    return {
        "checks": checks,
        "any_missing": len(missing) > 0,
        "hard_missing": len(hard_missing) > 0,
        "issues": [
            f"{c['name']}: {c['detail']} ({c['required_for']})" for c in missing
        ],
        "hard_issues": [
            f"{c['name']}: {c['detail']} ({c['required_for']})" for c in hard_missing
        ],
    }


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

    count = Carrier.objects.filter(is_active=True).count()
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

    if EmailTemplate.objects.count() < 1:
        issues.append("Create at least one email template.")

    env = env_api_key_status()
    for c in env["checks"]:
        if c["name"].startswith("MJ_APIKEY") and not c["ok"]:
            issues.append(f"{c['name']} is not set properly in /etc/boxes.env.")

    return SetupItem(
        key="emails",
        label="Emails",
        url_name="email_settings",
        required=False,
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
    required = bool(gs.email_sending)
    # Empty subject/content still "exists" but warn
    empty = EmailTemplate.objects.filter(subject="").count() + EmailTemplate.objects.filter(content="").count()
    if count >= 1 and empty > 0:
        issues.append("One or more email templates have an empty subject or body.")
    return SetupItem(
        key="email_templates",
        label="Email Templates",
        url_name="email_template",
        required=required,
        ok=count >= 1 and empty == 0,
        issues=issues,
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
    env = env_api_key_status()
    issues = []
    for c in env["checks"]:
        if c["name"].startswith("STRIPE_") and not c["ok"]:
            issues.append(f"{c['name']}: {c['detail']} — set in /etc/boxes.env")
    return SetupItem(
        key="stripe",
        label="Stripe Totals",
        url_name="stripe_totals",
        required=False,
        ok=len(issues) == 0,
        issues=issues,
        url=_url("stripe_totals"),
    )


def _check_env_keys() -> SetupItem:
    """Dedicated Management item for environment/API keys (not DB settings)."""
    env = env_api_key_status()
    # Show under General as well via banner; menu key for completeness
    return SetupItem(
        key="env_keys",
        label="API keys (/etc/boxes.env)",
        url_name="general_settings",
        required=False,
        ok=not env["hard_missing"],
        issues=env["hard_issues"] or (
            env["issues"] if env["any_missing"] else []
        ),
        url=_url("general_settings"),
    )


def compute_setup_status(*, use_cache: bool = True) -> dict[str, Any]:
    """Return full setup status dict for navbar and API."""
    if use_cache:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached

    builders = [
        ("accounts", None),
        ("env_keys", _check_env_keys),
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

    for key, builder in builders:
        if builder is None:
            continue
        item = builder()
        item.url = item.url or _url(item.url_name)
        items[item.key] = item.to_dict()
        order.append(item.key)

    required_issues: list[str] = []
    all_issues: list[str] = []
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

    env = env_api_key_status()

    result = {
        "items": items,
        "order": order,
        "required_incomplete": required_incomplete,
        "any_incomplete": any_incomplete,
        "required_issues": required_issues,
        "all_issues": all_issues,
        "env_api_keys": env,
    }
    cache.set(CACHE_KEY, result, CACHE_TTL_SECONDS)
    return result


def setup_status_for_template() -> dict[str, Any]:
    """Lightweight dict for templates (navbar)."""
    return compute_setup_status(use_cache=True)
