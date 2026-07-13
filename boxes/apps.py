from django.apps import AppConfig


class BoxesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "boxes"

    def ready(self):
        # Configure Stripe once at app startup instead of per-module import side effects
        from django.conf import settings
        import stripe

        if settings.STRIPE_API_KEY:
            stripe.api_key = settings.STRIPE_API_KEY
