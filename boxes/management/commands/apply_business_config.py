"""Load recommended Mike's Parcel defaults for empty charge/email/pickup config."""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from boxes.backend.setup_status import invalidate_setup_status_cache
from boxes.models import (
    AccountChargeSettings,
    Carrier,
    EmailSettings,
    EmailTemplate,
    GlobalSettings,
    NotificationRule,
    PackageType,
    PickupScheduleRule,
)


class Command(BaseCommand):
    help = "Apply recommended business configuration (idempotent; non-secret)."

    def handle(self, *args, **options):
        with transaction.atomic():
            gs = GlobalSettings.load()
            desired = {
                "name": "Mike's Parcel",
                "address1": "373 West Stutsman Street",
                "address2": "Pembina, North Dakota 58271",
                "website": "https://mikesparcelpickup.com/",
                "email": "mikesparcelpickup@gmail.com",
                "phone_number": "+1 (701) 599-0440",
            }
            for k, v in desired.items():
                cur = getattr(gs, k, None)
                if cur is None or (isinstance(cur, str) and not str(cur).strip()) or (
                    k == "name" and str(cur).strip() in ("Boxes", "")
                ):
                    setattr(gs, k, v)
            gs.email_sending = True
            gs.save()

            body = (
                "<p>Hello {first_name},</p>"
                "<p>A package has been checked in for you at Mike's Parcel Pickup.</p>"
                "<p><strong>Tracking:</strong> {tracking_code}<br>"
                "<strong>Carrier:</strong> {carrier}</p>"
                "<p>{comment}</p>"
                "<p>373 West Stutsman Street<br>Pembina, ND 58271<br>"
                "+1 (701) 599-0440</p>"
            )
            tmpl, _ = EmailTemplate.objects.get_or_create(
                name="Check In",
                defaults={"subject": "Your package has been checked in", "content": body},
            )
            if not (tmpl.subject or "").strip() or not (tmpl.content or "").strip():
                tmpl.subject = "Your package has been checked in"
                tmpl.content = body
                tmpl.save()

            es = EmailSettings.objects.order_by("pk").first()
            if es is None:
                es = EmailSettings.objects.create(
                    sender_name="Mike's Parcel Pickup",
                    sender_email="mikesparcelpickup@gmail.com",
                    check_in_template=tmpl,
                )
            else:
                if not es.sender_name:
                    es.sender_name = "Mike's Parcel Pickup"
                if not es.sender_email:
                    es.sender_email = "mikesparcelpickup@gmail.com"
                if es.check_in_template_id is None:
                    es.check_in_template = tmpl
                es.save()

            for days in (75, 90, 165, 180):
                NotificationRule.objects.get_or_create(
                    email_settings=es, days=days, defaults={"template": tmpl}
                )

            if not AccountChargeSettings.objects.filter(
                days=90, package_type_id__isnull=True, price__isnull=True,
                frequency__isnull=True, endpoint__isnull=True,
            ).exists():
                AccountChargeSettings.objects.create(days=90)
            if not AccountChargeSettings.objects.filter(endpoint__isnull=False).exists():
                AccountChargeSettings.objects.create(endpoint=180)
            pallet = PackageType.objects.filter(shortcode="P").first()
            if pallet and not AccountChargeSettings.objects.filter(
                package_type=pallet, days=30, frequency="D"
            ).exists():
                AccountChargeSettings.objects.create(
                    package_type=pallet, days=30, price=Decimal("2.00"), frequency="D"
                )

            start = date(2024, 1, 1)
            for weekday, label in enumerate(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            ):
                PickupScheduleRule.objects.get_or_create(
                    name=f"Weekday pickups — {label}",
                    defaults={
                        "recurrence": PickupScheduleRule.RECURRENCE_WEEKLY,
                        "weekday": weekday,
                        "start_date": start,
                        "is_active": True,
                    },
                )

            Carrier.objects.filter(name="DbgC").update(is_active=False)
            PackageType.objects.filter(shortcode="D").update(is_active=False)

        invalidate_setup_status_cache()
        self.stdout.write(self.style.SUCCESS("Applied recommended business configuration."))
