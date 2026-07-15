"""External webhook receivers."""
import logging
import stripe
from boxes.tasks.stripe import handle_stripe_webhook
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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
