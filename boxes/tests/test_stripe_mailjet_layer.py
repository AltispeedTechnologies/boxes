"""Layer tests for Stripe webhook serialization and Mailjet send path config."""
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase, override_settings

from boxes.models import Invoice
from boxes.tasks.stripe import handle_stripe_webhook, process_successful_invoice
from boxes.tests.helpers import link_user, make_account, make_package, make_user


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False, STRIPE_WEBHOOK_SECRET="whsec_test")
class StripeWebhookLayerTest(TestCase):
    def setUp(self):
        self.user = make_user(username="payuser", groups=["Customer"])
        self.account = make_account(user=self.user, balance=Decimal("-12.00"))
        link_user(self.user, self.account)
        self.package = make_package(self.account, price=Decimal("6.00"), paid=False)
        self.invoice = Invoice.objects.create(
            user=self.user,
            account=self.account,
            payment_intent_id="pi_test_123",
            subtotal=Decimal("6.00"),
            current_state=1,
            line_items=[{"id": self.package.id, "amt": 6.0, "late": False, "prtl": False}],
        )

    def test_process_successful_invoice_marks_paid(self):
        process_successful_invoice(
            self.user.id,
            self.account.id,
            self.invoice.id,
            self.invoice.subtotal,
            self.invoice.line_items,
        )
        self.package.refresh_from_db()
        self.assertTrue(self.package.paid)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_handle_stripe_webhook_succeeded(self, delay_mock):
        handle_stripe_webhook({
            "id": "pi_test_123",
            "status": "succeeded",
        })
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.current_state, 3)
        delay_mock.assert_called()

    @patch("boxes.tasks.stripe.handle_stripe_webhook.delay")
    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_serializes_object(self, construct, delay_mock):
        pi = MagicMock()
        pi.to_dict_recursive.return_value = {"id": "pi_x", "status": "succeeded"}
        event = MagicMock()
        event.type = "payment_intent.succeeded"
        event.data.object = pi
        construct.return_value = event

        client = Client()
        response = client.post(
            "/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
        )
        self.assertEqual(response.status_code, 200)
        delay_mock.assert_called_once_with({"id": "pi_x", "status": "succeeded"})


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class MailjetSendConfigTest(TestCase):
    @patch("boxes.tasks.emails.GlobalSettings.load")
    def test_send_emails_requires_keys(self, load_mock):
        from boxes.tasks.emails import send_emails

        gs = MagicMock()
        gs.email_sending = True
        load_mock.return_value = gs

        with self.settings(MJ_APIKEY_PUBLIC=None, MJ_APIKEY_PRIVATE=None):
            with patch.dict("os.environ", {}, clear=False):
                # Ensure env keys absent
                import os
                os.environ.pop("MJ_APIKEY_PUBLIC", None)
                os.environ.pop("MJ_APIKEY_PRIVATE", None)
                with self.assertRaises(RuntimeError):
                    send_emails()
