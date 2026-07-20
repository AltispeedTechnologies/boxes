"""Mailjet notification sending from EmailQueue."""
import os
import json
import re
from boxes.models import (
    CustomUserEmail, EmailQueue, EmailSettings, GlobalSettings, Package, SentEmail,
    SentEmailContents, SentEmailPackage, SentEmailResult, UserAccount
)
from celery import shared_task
from django.conf import settings
from django.db import transaction
from html import unescape
from mailjet_rest import Client


TOKEN_KEYS = (
    "first_name",
    "last_name",
    "full_name",
    "tracking_code",
    "carrier",
    "comment",
)

# Legacy chip labels (display text) mapped to token keys
_LEGACY_LABEL_TO_TOKEN = {
    "first_name": "first_name",
    "last_name": "last_name",
    "full_name": "full_name",
    "tracking_code": "tracking_code",
    "carrier": "carrier",
    "comment": "comment",
}


def _fetch_candidates():
    """Select EmailQueue rows ready to process."""
    candidates = {}
    template_objs = {}

    with transaction.atomic():
        queue_items = list(EmailQueue.objects.select_for_update().select_related("package__account", "template").all())
        for item in queue_items:
            account_id = item.package.account.id
            package_id = item.package.id
            template = item.template

            if account_id not in candidates:
                candidates[account_id] = {}
            if template.id not in candidates[account_id]:
                candidates[account_id][template.id] = []
                template_objs[template.id] = template
            candidates[account_id][template.id].append(package_id)

            item.delete()

    return candidates, template_objs


def _send_email(email_data):
    """Send one email payload via Mailjet; record SentEmail* rows."""
    email_payload = {
        "Messages": [
            {
                "From": {"Email": email_data["email_settings"].sender_email,
                         "Name": email_data["email_settings"].sender_name},
                "To": [{"Email": email_data["recipient_email"], "Name": email_data["hr_name"]}],
                "Subject": email_data["subject"],
                "TextPart": email_data["email_text"],
                "HTMLPart": email_data["email_html"]
            }
        ]
    }

    # Send the email
    result = email_data["mailjet"].send.create(data=email_payload)

    # Interpret the immediate result and store it for later analysis
    json_result = result.json()
    json_message = json_result["Messages"][0]
    success = json_message["Status"] == "success"
    message_uuid = json_message["To"][0]["MessageUUID"] if success else None

    # Create main SentEmail object
    sent_email = SentEmail.objects.create(
        account_id=email_data["account_id"],
        subject=email_data["subject"],
        email=email_data["recipient_email"],
        success=success,
        message_uuid=message_uuid
    )
    # Store the contents of the sent email
    SentEmailContents.objects.create(sent_email=sent_email, html=email_data["email_html"])
    # Ensure each package can have a record of a sent email
    for package_id in email_data["package_ids"]:
        SentEmailPackage.objects.create(sent_email=sent_email, package_id=package_id)
    # Store the raw JSON result, in case something goes haywire
    SentEmailResult.objects.create(sent_email=sent_email, response=json_result)


def _token_replacements(user, tracking_code, carrier_name, comment):
    """Build explicit token → value map for safe substitution."""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "tracking_code": tracking_code or "",
        "carrier": carrier_name or "",
        "comment": comment or "",
    }


def _apply_token_replacements(text, replacements):
    """Substitute template tokens without str.format (braces-safe).

    Supports:
    - Chips with data-token="first_name"
    - Legacy custom-block chips whose inner text is a display label
    - Literal {token} placeholders in subject/body
    """
    if not text:
        return ""

    def chip_data_token(match):
        token = match.group(1)
        if token in replacements:
            return str(replacements[token])
        return match.group(0)

    # Prefer stable data-token chips
    text = re.sub(
        r'<span\b[^>]*\bdata-token=["\']([a-z_]+)["\'][^>]*>.*?</span>',
        chip_data_token,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    def legacy_chip(match):
        label = match.group(1).strip().lower().replace(" ", "_")
        token = _LEGACY_LABEL_TO_TOKEN.get(label)
        if token and token in replacements:
            return str(replacements[token])
        return match.group(0)

    # Legacy chips: class contains custom-block, inner text is the label
    text = re.sub(
        r'<span\b[^>]*class=["\'][^"\']*custom-block[^"\']*["\'][^>]*>([^<]+)</span>',
        legacy_chip,
        text,
        flags=re.IGNORECASE,
    )

    # Explicit placeholder replace — never str.format on full HTML
    for key in TOKEN_KEYS:
        text = text.replace("{" + key + "}", str(replacements[key]))

    return text


def _html_to_plaintext(email_html):
    """Convert HTML body to plain text; br/p become newlines before tag strip."""
    email_text = email_html or ""
    email_text = re.sub(r"<br\s*/?>", "\n", email_text, flags=re.IGNORECASE)
    email_text = re.sub(r"</p\s*>", "\n", email_text, flags=re.IGNORECASE)
    email_text = re.sub(r"<p\b[^>]*>", "", email_text, flags=re.IGNORECASE)
    email_text = re.sub(r"<[^>]+>", "", email_text)
    email_text = unescape(email_text)
    return email_text


def _prepare_email_content(user, template, tracking_code, carrier_name, comment):
    """Render template subject/body for a user and package context.

    Returns (hr_name, email_html, email_text, subject) with tokens substituted
    in both subject and HTML body. Plain text is derived after br/p → newlines.
    """
    replacements = _token_replacements(user, tracking_code, carrier_name, comment)
    hr_name = replacements["full_name"] or f"{user.first_name} {user.last_name}".strip()

    email_html = _apply_token_replacements(template.content, replacements)
    subject = _apply_token_replacements(template.subject, replacements)
    email_text = _html_to_plaintext(email_html)

    return hr_name, email_html, email_text, subject


def _send_users(users, email_data):
    """Send prepared content to each user notification address."""
    for user in users:
        hr_name, email_html, email_text, subject = _prepare_email_content(
            user,
            email_data["template"],
            email_data["tracking_code"],
            email_data["carrier_name"],
            email_data["comment"],
        )

        for recipient_email_obj in CustomUserEmail.objects.filter(user=user):
            email_data.update({
                "hr_name": hr_name,
                "email_html": email_html,
                "email_text": email_text,
                "subject": subject,
                "recipient_email": recipient_email_obj.email,
            })
            _send_email(email_data)


@shared_task
def send_emails():
    # Do not proceed if email sending is disabled
    """Celery beat: drain queue if GlobalSettings.email_sending is enabled."""
    global_settings = GlobalSettings.load()
    if not global_settings.email_sending:
        return

    candidates, template_objs = _fetch_candidates()
    email_settings = EmailSettings.objects.first()

    api_key = getattr(settings, "MJ_APIKEY_PUBLIC", None) or os.environ.get("MJ_APIKEY_PUBLIC")
    api_secret = getattr(settings, "MJ_APIKEY_PRIVATE", None) or os.environ.get("MJ_APIKEY_PRIVATE")
    if not api_key or not api_secret:
        raise RuntimeError("Mailjet API keys not configured (MJ_APIKEY_PUBLIC/PRIVATE)")
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")

    for account_id, templates in candidates.items():
        user_accounts = UserAccount.objects.filter(
            account__id=account_id, is_active=True
        ).select_related("user")
        users = [ua.user for ua in user_accounts if ua.user.is_active]

        for template_id, package_ids in templates.items():
            template = template_objs[template_id]
            results = Package.objects.filter(pk__in=package_ids).values_list("tracking_code", "carrier__name",
                                                                             "comments")

            if results:
                tracking_codes = [result[0] for result in results]
                carrier_names = [result[1] for result in results]
                comments = [result[2] for result in results]

                tracking_code = ", ".join(tracking_codes)
                carrier_name = ", ".join(set(carrier_names))
                comment = "\n".join(comments)

                email_data = {
                    "template": template,
                    "tracking_code": tracking_code,
                    "carrier_name": carrier_name,
                    "package_ids": package_ids,
                    "email_settings": email_settings,
                    "mailjet": mailjet,
                    "account_id": account_id,
                    "comment": comment
                }

                _send_users(users, email_data)
