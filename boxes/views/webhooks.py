"""External webhook receivers."""
import base64
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


@require_http_methods(["POST"])
@csrf_exempt
def stripe_webhooks(request):
    """POST: verify Stripe signature and enqueue payment handling."""
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            request.body, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        logger.warning("Error parsing Stripe payload: %s", e)
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError as e:
        logger.warning("Error verifying Stripe webhook signature: %s", e)
        return HttpResponse(status=400)

    # This endpoint only supports PaymentIntent objects with specific events
    valid_payment_intent_types = ["succeeded", "canceled", "payment_failed"]
    if not (event.type.startswith("payment_intent") and event.type.split(".")[1] in valid_payment_intent_types):
        return HttpResponse(status=400)

    handle_stripe_webhook.delay(event.data.object)

    return HttpResponse(status=200)


def _mailjet_auth_ok(request):
    """Validate Mailjet webhook via shared secret and/or HTTP basic auth.

    If MAILJET_WEBHOOK_SECRET is set, require it via header or ``?secret=``.
    Else if MAILJET_WEBHOOK_USER/PASSWORD are set, require HTTP basic auth.
    If neither is configured, accept (development) and log a warning.
    """
    secret = getattr(settings, "MAILJET_WEBHOOK_SECRET", None) or ""
    user = getattr(settings, "MAILJET_WEBHOOK_USER", None) or ""
    password = getattr(settings, "MAILJET_WEBHOOK_PASSWORD", None) or ""

    if secret:
        provided = (
            request.headers.get("X-Mailjet-Webhook-Secret")
            or request.META.get("HTTP_X_MAILJET_WEBHOOK_SECRET")
            or request.GET.get("secret")
            or ""
        )
        if provided and provided == secret:
            return True
        # Also accept basic auth when user/password are configured alongside secret
        if user and password and _basic_auth_matches(request, user, password):
            return True
        logger.warning("Mailjet webhook auth failed (shared secret)")
        return False

    if user and password:
        if _basic_auth_matches(request, user, password):
            return True
        logger.warning("Mailjet webhook auth failed (basic auth)")
        return False

    logger.warning(
        "Mailjet webhook accepted without credentials; "
        "set MAILJET_WEBHOOK_SECRET or MAILJET_WEBHOOK_USER/PASSWORD"
    )
    return True


def _basic_auth_matches(request, expected_user, expected_password):
    """Return True if Authorization: Basic matches expected credentials."""
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
        username, _, passwd = decoded.partition(":")
    except (ValueError, UnicodeDecodeError) as e:
        logger.warning("Mailjet webhook basic auth decode error: %s", e)
        return False
    return username == expected_user and passwd == expected_password


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
    """
    if not _mailjet_auth_ok(request):
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body.decode("utf-8") or "[]")
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.warning("Error parsing Mailjet webhook payload: %s", e)
        return HttpResponse(status=400)

    # Grouped events are a list; a single object is also accepted
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
