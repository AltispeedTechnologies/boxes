"""External webhook receivers (Stripe payments, Mailjet Event API)."""
import json
import logging
from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import force_str
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from boxes.models import SentEmail, SentEmailEvent
from boxes.tasks.stripe import handle_stripe_webhook

logger = logging.getLogger(__name__)

# Events we act on. Others return 200 so Stripe does not retry forever.
_STRIPE_HANDLED_TYPES = frozenset({
    "payment_intent.succeeded",
    "payment_intent.canceled",
    "payment_intent.payment_failed",
})


@require_http_methods(["POST"])
@csrf_exempt
def stripe_webhooks(request):
    """POST: verify Stripe signature and enqueue payment handling.

    Requires ``STRIPE_WEBHOOK_SECRET`` (``whsec_…``). Handled event types:
    ``payment_intent.succeeded``, ``payment_intent.canceled``,
    ``payment_intent.payment_failed``. Other verified events return 200 no-op.
    """
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None) or ""
    if not secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured")
        return HttpResponse(status=500)

    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(request.body, sig_header, secret)
    except ValueError as e:
        logger.warning("Error parsing Stripe payload: %s", e)
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError as e:
        logger.warning("Error verifying Stripe webhook signature: %s", e)
        return HttpResponse(status=400)

    if event.type not in _STRIPE_HANDLED_TYPES:
        logger.debug("Ignoring unhandled Stripe event type: %s", event.type)
        return HttpResponse(status=200)

    payment_intent = event.data.object
    if hasattr(payment_intent, "to_dict_recursive"):
        payment_intent = payment_intent.to_dict_recursive()
    elif hasattr(payment_intent, "to_dict"):
        payment_intent = payment_intent.to_dict()

    # payment_failed maps to requires_payment_method-style failure in handler
    if isinstance(payment_intent, dict) and event.type == "payment_intent.payment_failed":
        payment_intent = dict(payment_intent)
        if payment_intent.get("status") not in (
            "requires_payment_method",
            "canceled",
            "succeeded",
        ):
            payment_intent["status"] = "requires_payment_method"

    handle_stripe_webhook.delay(payment_intent)
    return HttpResponse(status=200)


def _mailjet_auth_ok(request):
    """Validate Mailjet Event API webhook via shared secret only.

    Set ``MAILJET_WEBHOOK_SECRET`` in ``/etc/boxes.env`` and the same value on
    the Mailjet Event API callback URL as ``?secret=...``.

    When the secret is unset: allow only if Django ``DEBUG`` is True (local
    development). Production-like runs reject unauthenticated webhooks.
    """
    secret = getattr(settings, "MAILJET_WEBHOOK_SECRET", None) or ""
    if not secret:
        if getattr(settings, "DEBUG", False):
            logger.warning(
                "Mailjet webhook accepted without credentials (DEBUG); "
                "set MAILJET_WEBHOOK_SECRET in /etc/boxes.env and use "
                "?secret= on the Mailjet Event API callback URL"
            )
            return True
        logger.error(
            "MAILJET_WEBHOOK_SECRET is not configured; rejecting Mailjet webhook"
        )
        return False

    provided = (
        request.headers.get("X-Mailjet-Webhook-Secret")
        or request.META.get("HTTP_X_MAILJET_WEBHOOK_SECRET")
        or request.GET.get("secret")
        or ""
    )
    if provided and provided == secret:
        return True
    logger.warning("Mailjet webhook auth failed (shared secret mismatch or missing)")
    return False


def _parse_event_timestamp(raw_time):
    """Convert Mailjet unix timestamp (or ISO string) to aware datetime."""
    if raw_time is None:
        return datetime.now(tz=dt_timezone.utc)
    if isinstance(raw_time, (int, float)):
        return datetime.fromtimestamp(raw_time, tz=dt_timezone.utc)
    if isinstance(raw_time, str) and raw_time.isdigit():
        return datetime.fromtimestamp(int(raw_time), tz=dt_timezone.utc)
    try:
        return datetime.fromisoformat(force_str(raw_time).replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(tz=dt_timezone.utc)


def _process_mailjet_event(event):
    """Persist one Mailjet event dict as SentEmailEvent, linked when possible."""
    if not isinstance(event, dict):
        logger.warning("Skipping non-dict Mailjet event: %r", event)
        return

    event_type = event.get("event") or event.get("EventType") or "unknown"
    message_uuid = (
        event.get("Message_GUID")
        or event.get("MessageUUID")
        or event.get("message_uuid")
    )
    if message_uuid is not None:
        message_uuid = str(message_uuid)

    sent_email = None
    if message_uuid:
        sent_email = SentEmail.objects.filter(message_uuid=message_uuid).first()

    SentEmailEvent.objects.create(
        sent_email=sent_email,
        event_type=str(event_type)[:32],
        timestamp=_parse_event_timestamp(event.get("time")),
        message_uuid=message_uuid,
        email=event.get("email"),
        payload=event,
    )


@require_http_methods(["POST"])
@csrf_exempt
def mailjet_webhooks(request):
    """POST: accept Mailjet Event API payloads and store SentEmailEvent rows.

    Maps each event to SentEmail by Message_GUID / MessageUUID when present.
    Auth: ``MAILJET_WEBHOOK_SECRET`` via ``?secret=`` on the Event API URL.
    """
    if not _mailjet_auth_ok(request):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body.decode("utf-8") or "[]")
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("Error parsing Mailjet webhook payload: %s", e)
        return HttpResponse(status=400)

    if isinstance(payload, dict):
        events = [payload]
    elif isinstance(payload, list):
        events = payload
    else:
        logger.warning("Unexpected Mailjet payload type: %s", type(payload))
        return HttpResponse(status=400)

    for event in events:
        try:
            _process_mailjet_event(event)
        except Exception:
            logger.exception("Failed to process Mailjet event: %r", event)

    return HttpResponse(status=200)
