"""Unit and integration tests for Stripe customer payments and webhooks."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase, override_settings

from boxes.models import AccountLedger, Invoice, Package
from boxes.tasks.stripe import (
    apply_invoice_success,
    handle_stripe_webhook,
    process_successful_invoice,
    sync_invoice_from_payment_intent,
)
from boxes.tests.helpers import link_user, make_account, make_package, make_user


def _invoice(user, account, package, pi_id="pi_test_123", state=1, amount=6.0):
    return Invoice.objects.create(
        user=user,
        account=account,
        payment_intent_id=pi_id,
        subtotal=Decimal(str(amount)),
        current_state=state,
        line_items=[{"id": package.id, "amt": float(amount), "late": False, "prtl": False, "qty": 1, "desc": "Box"}],
    )


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False, STRIPE_WEBHOOK_SECRET="whsec_test")
class ApplyInvoiceSuccessTests(TestCase):
    def setUp(self):
        self.user = make_user(username="pay_ok", groups=["Customer"])
        self.account = make_account(user=self.user, balance=Decimal("-12.00"))
        link_user(self.user, self.account)
        self.package = make_package(self.account, price=Decimal("6.00"), paid=False)
        self.invoice = _invoice(self.user, self.account, self.package)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_apply_success_marks_paid_and_ledger(self, delay_mock):
        applied = apply_invoice_success(self.invoice)
        self.assertTrue(applied)
        self.package.refresh_from_db()
        self.invoice.refresh_from_db()
        self.assertTrue(self.package.paid)
        self.assertEqual(self.invoice.current_state, 3)
        self.assertEqual(AccountLedger.objects.filter(invoice=self.invoice).count(), 1)
        delay_mock.assert_called()

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_apply_success_is_idempotent(self, delay_mock):
        self.assertTrue(apply_invoice_success(self.invoice))
        self.assertFalse(apply_invoice_success(self.invoice))
        self.assertFalse(apply_invoice_success(self.invoice))
        self.assertEqual(AccountLedger.objects.filter(invoice=self.invoice).count(), 1)
        # total_accounts only on first apply
        self.assertEqual(delay_mock.call_count, 1)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_handle_webhook_succeeded_twice(self, delay_mock):
        payload = {"id": "pi_test_123", "status": "succeeded"}
        handle_stripe_webhook(payload)
        handle_stripe_webhook(payload)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.current_state, 3)
        self.assertEqual(AccountLedger.objects.filter(invoice=self.invoice).count(), 1)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_handle_webhook_failed_sets_state_4(self, delay_mock):
        handle_stripe_webhook({"id": "pi_test_123", "status": "requires_payment_method"})
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.current_state, 4)
        self.assertFalse(Package.objects.get(pk=self.package.pk).paid)

    def test_handle_webhook_canceled_deletes_unsettled(self):
        handle_stripe_webhook({"id": "pi_test_123", "status": "canceled"})
        self.assertFalse(Invoice.objects.filter(pk=self.invoice.pk).exists())

    @patch("boxes.tasks.stripe.total_accounts.delay")
    def test_canceled_does_not_delete_settled(self, delay_mock):
        apply_invoice_success(self.invoice)
        handle_stripe_webhook({"id": "pi_test_123", "status": "canceled"})
        self.assertTrue(Invoice.objects.filter(pk=self.invoice.pk).exists())

    def test_unknown_payment_intent_noop(self):
        handle_stripe_webhook({"id": "pi_unknown", "status": "succeeded"})
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.current_state, 1)

    def test_sync_processing(self):
        sync_invoice_from_payment_intent(self.invoice, {"status": "processing"})
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.current_state, 2)


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False, STRIPE_WEBHOOK_SECRET="whsec_test")
class StripeWebhookHTTPTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("boxes.tasks.stripe.handle_stripe_webhook.delay")
    @patch("stripe.Webhook.construct_event")
    def test_handled_event_enqueues(self, construct, delay_mock):
        pi = MagicMock()
        pi.to_dict_recursive.return_value = {"id": "pi_x", "status": "succeeded"}
        event = MagicMock()
        event.type = "payment_intent.succeeded"
        event.data.object = pi
        construct.return_value = event

        r = self.client.post(
            "/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
        )
        self.assertEqual(r.status_code, 200)
        delay_mock.assert_called_once_with({"id": "pi_x", "status": "succeeded"})

    @patch("boxes.tasks.stripe.handle_stripe_webhook.delay")
    @patch("stripe.Webhook.construct_event")
    def test_unhandled_event_returns_200_no_enqueue(self, construct, delay_mock):
        event = MagicMock()
        event.type = "customer.created"
        event.data.object = MagicMock()
        construct.return_value = event

        r = self.client.post(
            "/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
        )
        self.assertEqual(r.status_code, 200)
        delay_mock.assert_not_called()

    @patch("stripe.Webhook.construct_event", side_effect=Exception("nope"))
    def test_bad_signature_400(self, construct):
        import stripe as stripe_mod

        construct.side_effect = stripe_mod.SignatureVerificationError("bad", "sig")
        r = self.client.post(
            "/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=bad",
        )
        self.assertEqual(r.status_code, 400)

    @patch("boxes.tasks.stripe.handle_stripe_webhook.delay")
    @patch("stripe.Webhook.construct_event")
    def test_payment_failed_normalizes_status(self, construct, delay_mock):
        pi = MagicMock()
        pi.to_dict_recursive.return_value = {"id": "pi_f", "status": "requires_action"}
        event = MagicMock()
        event.type = "payment_intent.payment_failed"
        event.data.object = pi
        construct.return_value = event

        r = self.client.post(
            "/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=abc",
        )
        self.assertEqual(r.status_code, 200)
        args = delay_mock.call_args[0][0]
        self.assertEqual(args["status"], "requires_payment_method")


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    STRIPE_WEBHOOK_SECRET="whsec_test",
    STRIPE_SECRET_KEY="sk_test_x",
)
class CustomerPaymentFlowHTTPTests(TestCase):
    """Integration-style tests of customer payment endpoints (Stripe mocked)."""

    def setUp(self):
        self.client = Client()
        self.user = make_user(username="cust_pay", groups=["Customer"])
        self.account = make_account(user=self.user, balance=Decimal("-10.00"))
        link_user(self.user, self.account)
        self.package = make_package(self.account, price=Decimal("10.00"), paid=False)
        self.client.force_login(self.user)
        # active account in session
        session = self.client.session
        session["active_account_id"] = self.account.id
        session.save()

    def test_make_payment_page_loads(self):
        with patch("boxes.backend.invoice.get_payment_methods", return_value=([], None)):
            with patch("boxes.backend.invoice.generate_line_items", return_value=[]):
                r = self.client.get("/customer/payments")
        self.assertEqual(r.status_code, 200)

    def test_new_invoice_rejects_small_amount(self):
        r = self.client.post(
            "/invoice/new",
            data='{"amount": 0.10, "method": "ONETIME"}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()["success"])

    def test_new_invoice_rejects_bad_json(self):
        r = self.client.post(
            "/invoice/new",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    @patch("boxes.backend.invoice.generate_line_items")
    @patch("boxes.backend.invoice.get_customer_id", return_value="cus_test")
    @patch("stripe.PaymentIntent.create")
    def test_new_invoice_saved_method_creates_pi(self, pi_create, _cust, gen_li):
        from boxes.models import AccountStripeCustomer, StripePaymentMethod

        gen_li.return_value = [
            {"id": self.package.id, "amt": 10.0, "late": False, "prtl": False, "qty": 1, "desc": "Box"}
        ]
        pi_create.return_value = MagicMock(id="pi_new_1")
        sc = AccountStripeCustomer.objects.create(
            account=self.account, customer_id="cus_test"
        )
        pm = StripePaymentMethod.objects.create(
            customer=sc, payment_method_id="pm_card_1"
        )

        with patch("boxes.models.GlobalSettings.load") as gs:
            g = MagicMock()
            g.taxes = False
            g.tax_rate = 0
            g.pass_on_fees = False
            g.tax_stripe_id = None
            gs.return_value = g
            r = self.client.post(
                "/invoice/new",
                data=f'{{"amount": 10.00, "method": {pm.pk}}}',
                content_type="application/json",
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["success"])
        inv = Invoice.objects.get(payment_intent_id="pi_new_1")
        self.assertEqual(inv.account_id, self.account.id)
        self.assertEqual(inv.user_id, self.user.id)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    @patch("stripe.PaymentIntent.retrieve")
    def test_view_invoice_settles_on_succeeded_pi(self, retrieve, delay_mock):
        inv = _invoice(self.user, self.account, self.package, pi_id="pi_view_1", state=1)
        retrieve.return_value = {
            "id": "pi_view_1",
            "status": "succeeded",
            "payment_method": None,
            "last_payment_error": None,
        }
        r = self.client.get(f"/invoice/{inv.pk}")
        self.assertEqual(r.status_code, 200)
        inv.refresh_from_db()
        self.assertEqual(inv.current_state, 3)
        self.package.refresh_from_db()
        self.assertTrue(self.package.paid)

    @patch("boxes.tasks.stripe.total_accounts.delay")
    @patch("stripe.PaymentIntent.confirm")
    def test_confirm_succeeded_settles(self, confirm, delay_mock):
        inv = _invoice(self.user, self.account, self.package, pi_id="pi_conf_1", state=0)
        confirm.return_value = {
            "id": "pi_conf_1",
            "status": "succeeded",
            "next_action": None,
        }
        r = self.client.post(f"/invoice/{inv.pk}/confirm")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])
        inv.refresh_from_db()
        self.assertEqual(inv.current_state, 3)
        self.assertEqual(AccountLedger.objects.filter(invoice=inv).count(), 1)

    @patch("stripe.PaymentIntent.cancel")
    def test_cancel_deletes_unsettled_invoice(self, cancel_mock):
        inv = _invoice(self.user, self.account, self.package, pi_id="pi_can_1", state=0)
        r = self.client.get(f"/invoice/{inv.pk}/cancel")
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Invoice.objects.filter(pk=inv.pk).exists())
        cancel_mock.assert_called_once_with("pi_can_1")

    @patch("boxes.tasks.stripe.total_accounts.delay")
    @patch("stripe.PaymentIntent.cancel")
    def test_cancel_keeps_settled_invoice(self, cancel_mock, delay_mock):
        inv = _invoice(self.user, self.account, self.package, pi_id="pi_can_2", state=1)
        apply_invoice_success(inv)
        r = self.client.get(f"/invoice/{inv.pk}/cancel")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Invoice.objects.filter(pk=inv.pk).exists())
        cancel_mock.assert_not_called()


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class MailjetWebhookSecretOnlyTests(TestCase):
    def setUp(self):
        self.client = Client()

    @override_settings(MAILJET_WEBHOOK_SECRET="s3cret")
    def test_requires_query_secret(self):
        r = self.client.post(
            "/webhooks/mailjet",
            data='[{"event":"bounce","time":1,"Message_GUID":"x"}]',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)
        r2 = self.client.post(
            "/webhooks/mailjet?secret=s3cret",
            data='[{"event":"bounce","time":1,"Message_GUID":"x"}]',
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 200)

    @override_settings(MAILJET_WEBHOOK_SECRET="s3cret")
    def test_basic_auth_no_longer_accepted(self):
        import base64

        token = base64.b64encode(b"u:p").decode()
        r = self.client.post(
            "/webhooks/mailjet",
            data='[{"event":"bounce","time":1}]',
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Basic {token}",
        )
        self.assertEqual(r.status_code, 401)

@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class CheckoutUiModeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user(username="ui_mode_user", groups=["Customer"])
        self.account = make_account(user=self.user, balance=Decimal("-5.00"))
        link_user(self.user, self.account)
        self.client.force_login(self.user)
        session = self.client.session
        session["active_account_id"] = self.account.id
        session.save()

    @patch("boxes.backend.invoice.generate_checkout_line_items", return_value=([], 0))
    @patch("boxes.backend.invoice.generate_line_items", return_value=[])
    @patch("boxes.backend.invoice.get_customer_id", return_value="cus_ui")
    @patch("stripe.checkout.Session.create")
    def test_onetime_uses_hosted_page_ui_mode(self, create, *_mocks):
        create.return_value = {"url": "https://checkout.stripe.com/c/pay/cs_test_x"}
        with patch("boxes.models.GlobalSettings.load") as gs:
            g = MagicMock()
            g.taxes = False
            g.tax_rate = 0
            g.pass_on_fees = False
            g.tax_stripe_id = None
            gs.return_value = g
            r = self.client.post(
                "/invoice/new",
                data='{"amount": 5.00, "method": "ONETIME"}',
                content_type="application/json",
            )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs.get("ui_mode"), "hosted_page")
        self.assertEqual(kwargs.get("mode"), "payment")
