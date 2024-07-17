import json
import stripe
from boxes.tasks.stripe import handle_stripe_webhook
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# Set the stripe API key from our local configuration
stripe.api_key = settings.STRIPE_API_KEY


@require_http_methods(["POST"])
@csrf_exempt
def stripe_webhooks(request):
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event = stripe.Event.construct_from(
            json.loads(request.body), sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    # Invalid payload
    except ValueError as e:
        print("Error parsing payload: {}".format(str(e)))
        return HttpResponse(status=400)
    # Invalid signature
    except stripe.error.SignatureVerificationError as e:
        print("Error verifying webhook signature: {}".format(str(e)))
        return HttpResponse(status=400)

    # This endpoint only supports PaymentIntent objects with specific events
    valid_payment_intent_types = ["succeeded", "canceled", "payment_failed"]
    if not (event.type.startswith("payment_intent") and event.type.split(".")[1] in valid_payment_intent_types):
        return HttpResponse(status=400)

    handle_stripe_webhook.delay(event.data.object, request.user.id)

    return HttpResponse(status=200)
