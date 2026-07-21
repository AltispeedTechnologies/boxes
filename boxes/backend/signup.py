"""Signup invite creation, email delivery, and token-gated registration."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from boxes.backend.account import create_billing_account, create_web_user
from boxes.models import (
    EmailSettings,
    GlobalSettings,
    SentEmail,
    SentEmailContents,
    SentEmailResult,
    UserAccount,
)
from boxes.models.signup import SignupInvite

logger = logging.getLogger(__name__)

DEFAULT_INVITE_DAYS = 14


def _normalize_email(email):
    email = (email or "").strip().lower()
    if not email:
        raise ValidationError({"email": ["Email is required."]})
    try:
        validate_email(email)
    except ValidationError as exc:
        raise ValidationError({"email": list(exc.messages)}) from exc
    return email


def create_signup_invite(
    *,
    email,
    actor=None,
    first_name="",
    last_name="",
    middle_name="",
    prefix="",
    suffix="",
    company="",
    phone_number="",
    mobile_number="",
    account=None,
    role=UserAccount.ROLE_OWNER,
    create_account=False,
    account_name=None,
    billable=True,
    comments=None,
    expires_days=DEFAULT_INVITE_DAYS,
):
    """Create a SignupInvite (and optionally a billing Account to link on accept).

    Does **not** create a CustomUser — the invitee registers via the signed link.
    Returns the SignupInvite instance.
    """
    email = _normalize_email(email)
    expires_days = max(1, int(expires_days or DEFAULT_INVITE_DAYS))

    with transaction.atomic():
        linked_account = account
        if create_account and linked_account is None:
            if actor is None:
                raise ValidationError({"actor": ["Staff user required to create an account."]})
            composed = " ".join(
                p for p in [prefix, first_name, middle_name, last_name, suffix] if p
            ).strip()
            display = (account_name or composed or email.split("@")[0]).strip()[:64]
            linked_account = create_billing_account(
                actor=actor,
                name=display,
                billable=billable,
                comments=comments,
            )

        invite = SignupInvite.objects.create(
            email=email,
            first_name=(first_name or "").strip()[:150],
            last_name=(last_name or "").strip()[:150],
            middle_name=(middle_name or "").strip()[:64],
            prefix=(prefix or "").strip()[:16],
            suffix=(suffix or "").strip()[:16],
            company=(company or "").strip()[:128],
            phone_number=(phone_number or "").strip()[:20],
            mobile_number=(mobile_number or "").strip()[:20],
            account=linked_account,
            role=role or UserAccount.ROLE_OWNER,
            created_by=actor,
            expires_at=timezone.now() + timedelta(days=expires_days),
        )
    return invite



def app_public_origin(request=None):
    """Absolute origin for in-app links (signup invites, etc.).

    Uses existing deployment config — not marketing ``GlobalSettings.website``:

    1. Request host when it is listed in ``ALLOWED_HOSTS``.
    2. Otherwise first non-local entry in ``ALLOWED_HOSTS`` with
       ``http``/``https`` from ``SECURE_SSL_REDIRECT``.
    """
    allowed = [h for h in (getattr(settings, "ALLOWED_HOSTS", None) or []) if h]

    if request is not None:
        try:
            host = request.get_host()  # may include :port
            host_name = host.split(":")[0]
            if host_name in allowed or "*" in allowed:
                return request.build_absolute_uri("/").rstrip("/")
            for a in allowed:
                if a.startswith(".") and (host_name == a[1:] or host_name.endswith(a)):
                    return request.build_absolute_uri("/").rstrip("/")
        except Exception:
            logger.debug("app_public_origin: could not use request host", exc_info=True)

    skip = {"*", "127.0.0.1", "localhost", ".localhost", "testserver"}
    for host in allowed:
        if host in skip or host.startswith("."):
            continue
        scheme = "https" if getattr(settings, "SECURE_SSL_REDIRECT", False) else "http"
        return f"{scheme}://{host}"
    return ""


def invite_signup_url(invite, request=None):
    """Absolute signup URL for email bodies (app host from ALLOWED_HOSTS)."""
    path = reverse("signup", kwargs={"token": invite.token})
    origin = app_public_origin(request)
    if origin:
        return f"{origin}{path}"
    logger.warning("invite_signup_url: no ALLOWED_HOSTS origin; email link is path-only")
    return path



def _sender_identity():
    """Return (from_email, from_name) for invite mail."""
    settings_row = EmailSettings.objects.first()
    if settings_row and settings_row.sender_email:
        return settings_row.sender_email, settings_row.sender_name or "Boxes"
    gs = GlobalSettings.load()
    if gs.email:
        return gs.email, gs.name or "Boxes"
    return settings.DEFAULT_FROM_EMAIL, "Boxes"


def _build_invite_email_bodies(invite, signup_url):
    """Return (subject, text_body, html_body) for a signup invite."""
    business = GlobalSettings.load().name or "Boxes"
    name = (invite.first_name or "").strip() or "there"
    expiry = timezone.localtime(invite.expires_at).strftime("%Y-%m-%d %H:%M %Z")
    subject = f"You are invited to register for {business}"
    text = (
        f"Hello {name},\n\n"
        f"You have been invited to create a portal account for {business}.\n\n"
        f"Open this link to register (it expires on {expiry}):\n\n"
        f"{signup_url}\n\n"
        f"If you did not expect this message, you can ignore it.\n"
    )
    html = (
        f"<p>Hello {name},</p>"
        f"<p>You have been invited to create a portal account for "
        f"<strong>{business}</strong>.</p>"
        f'<p><a href="{signup_url}">Complete your registration</a></p>'
        f"<p>This link expires on {expiry}.</p>"
        f"<p>If you did not expect this message, you can ignore it.</p>"
    )
    return subject, text, html


def _record_sent_email(
    *,
    account=None,
    subject,
    recipient,
    success,
    html="",
    message_uuid=None,
    response=None,
):
    """Write SentEmail (+ contents/result) so invite mail appears in email logs."""
    sent_email = SentEmail.objects.create(
        account=account,
        subject=subject or "",
        email=recipient or "",
        success=bool(success),
        message_uuid=message_uuid,
    )
    if html:
        SentEmailContents.objects.create(sent_email=sent_email, html=html)
    if response is not None:
        SentEmailResult.objects.create(sent_email=sent_email, response=response)
    return sent_email


def _send_via_mailjet(from_email, from_name, to_email, to_name, subject, text, html):
    """Send one message via Mailjet REST.

    Returns ``(success, response_body, message_uuid)``.
    """
    public = getattr(settings, "MJ_APIKEY_PUBLIC", None)
    private = getattr(settings, "MJ_APIKEY_PRIVATE", None)
    if not public or not private:
        return False, {"error": "Mailjet API keys not configured"}, None
    try:
        from mailjet_rest import Client
    except ImportError:
        return False, {"error": "mailjet_rest not installed"}, None

    mailjet = Client(auth=(public, private), version="v3.1")
    payload = {
        "Messages": [
            {
                "From": {"Email": from_email, "Name": from_name},
                "To": [{"Email": to_email, "Name": to_name or to_email}],
                "Subject": subject,
                "TextPart": text,
                "HTMLPart": html,
            }
        ]
    }
    result = mailjet.send.create(data=payload)
    try:
        body = result.json()
    except Exception:
        logger.exception("Mailjet invite send parse failed")
        return (
            False,
            {"error": "invalid_json", "status_code": getattr(result, "status_code", None)},
            None,
        )

    try:
        message = (body.get("Messages") or [{}])[0]
        success = message.get("Status") == "success"
        message_uuid = None
        if success:
            to_list = message.get("To") or []
            if to_list:
                message_uuid = to_list[0].get("MessageUUID")
        return success, body, message_uuid
    except Exception:
        logger.exception("Mailjet invite send status parse failed")
        return False, body, None


def send_signup_invite_email(invite, request=None):
    """Deliver the invite email. Returns True if a provider accepted the message.

    Honors GlobalSettings.email_sending. Tries Mailjet first, then Django
    ``send_mail``. Updates ``email_sent_at`` / ``last_error`` on the invite
    and records a ``SentEmail`` row for the email logs page.
    """
    gs = GlobalSettings.load()
    if not gs.email_sending:
        invite.last_error = "Email sending is disabled in Global Settings."
        invite.save(update_fields=["last_error"])
        return False

    signup_url = invite_signup_url(invite, request=request)
    subject, text, html = _build_invite_email_bodies(invite, signup_url)
    from_email, from_name = _sender_identity()
    to_name = " ".join(p for p in [invite.first_name, invite.last_name] if p).strip()
    account = invite.account  # may be None for user-only invites

    sent, mj_body, message_uuid = _send_via_mailjet(
        from_email, from_name, invite.email, to_name, subject, text, html
    )

    if sent:
        _record_sent_email(
            account=account,
            subject=subject,
            recipient=invite.email,
            success=True,
            html=html,
            message_uuid=message_uuid,
            response=mj_body or {"provider": "mailjet", "status": "success"},
        )
    else:
        try:
            n = send_mail(
                subject=subject,
                message=text,
                from_email=from_email,
                recipient_list=[invite.email],
                html_message=html,
                fail_silently=False,
            )
            sent = n > 0
            _record_sent_email(
                account=account,
                subject=subject,
                recipient=invite.email,
                success=sent,
                html=html,
                message_uuid=None,
                response={
                    "provider": "django",
                    "sent_count": n,
                    "mailjet": mj_body,
                },
            )
        except Exception as exc:
            logger.exception("Django send_mail failed for invite %s", invite.pk)
            invite.last_error = str(exc)[:512]
            invite.save(update_fields=["last_error"])
            _record_sent_email(
                account=account,
                subject=subject,
                recipient=invite.email,
                success=False,
                html=html,
                message_uuid=None,
                response={
                    "provider": "django",
                    "error": str(exc)[:512],
                    "mailjet": mj_body,
                },
            )
            return False

        if not sent:
            # django path already recorded; keep last_error below
            pass

    # Mailjet failed and no django branch recorded yet (should not happen after
    # the else above always records). If Mailjet-only path ever short-circuits:
    if not sent and not SentEmail.objects.filter(
        email=invite.email, subject=subject
    ).order_by("-id").exists():
        _record_sent_email(
            account=account,
            subject=subject,
            recipient=invite.email,
            success=False,
            html=html,
            message_uuid=None,
            response=mj_body or {"error": "send_failed"},
        )

    if sent:
        invite.email_sent_at = timezone.now()
        invite.last_error = ""
        invite.save(update_fields=["email_sent_at", "last_error"])
    else:
        invite.last_error = "Email provider did not accept the message."
        invite.save(update_fields=["last_error"])
    return sent


def get_valid_invite(token):
    """Return a usable SignupInvite or raise ValidationError."""
    token = (token or "").strip()
    if not token:
        raise ValidationError({"token": ["Invalid or missing sign-up link."]})
    invite = SignupInvite.objects.filter(token=token).select_related("account").first()
    if invite is None:
        raise ValidationError({"token": ["This sign-up link is invalid."]})
    if invite.used_at is not None:
        raise ValidationError({"token": ["This sign-up link has already been used."]})
    if invite.is_expired():
        raise ValidationError({"token": ["This sign-up link has expired."]})
    return invite


def complete_signup(
    *,
    token,
    username,
    password,
    password2=None,
    first_name=None,
    last_name=None,
    company=None,
    phone_number=None,
    mobile_number=None,
):
    """Create an active portal user from a valid invite token.

    Returns dict with user, invite, membership (optional). Raises ValidationError
    on bad token or form data.
    """
    invite = get_valid_invite(token)

    if password2 is not None and password != password2:
        raise ValidationError({"password": ["Passwords do not match."]})

    first = (first_name if first_name is not None else invite.first_name) or ""
    last = (last_name if last_name is not None else invite.last_name) or ""
    if not str(first).strip():
        first = invite.email.split("@")[0]

    with transaction.atomic():
        invite = SignupInvite.objects.select_for_update().get(pk=invite.pk)
        if not invite.is_usable():
            raise ValidationError({"token": ["This sign-up link is no longer valid."]})

        user, membership = create_web_user(
            username=username,
            password=password,
            first_name=first,
            last_name=last,
            middle_name=invite.middle_name,
            prefix=invite.prefix,
            suffix=invite.suffix,
            company=company if company is not None else invite.company,
            phone_number=phone_number if phone_number is not None else invite.phone_number,
            mobile_number=mobile_number if mobile_number is not None else invite.mobile_number,
            email=invite.email,
            is_active=True,
            account=invite.account,
            role=invite.role or UserAccount.ROLE_OWNER,
            actor=invite.created_by,
        )

        invite.used_at = timezone.now()
        invite.used_by = user
        invite.save(update_fields=["used_at", "used_by"])

    return {
        "user": user,
        "invite": invite,
        "membership": membership,
        "account": invite.account,
    }
