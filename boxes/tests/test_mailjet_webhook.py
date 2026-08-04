"""Tests for Mailjet webhook receiver and SentEmailEvent mapping."""
import base64
import json
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from boxes.models import SentEmail, SentEmailEvent
from boxes.tests.helpers import make_account


def _basic_header(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    MAILJET_WEBHOOK_SECRET=None,
    DEBUG=True,
)
class MailjetWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.account = make_account(name="Webhook Acct")
        self.sent = SentEmail.objects.create(
            account=self.account,
            subject="Hello",
            email="customer@example.com",
            success=True,
            message_uuid="1ab23cd4-e567-8901-2345-6789f0gh1i2j",
        )

    def test_maps_event_to_sent_email_by_message_uuid(self):
        payload = [
            {
                "event": "open",
                "time": 1433103519,
                "MessageID": 19421777396190490,
                "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
                "email": "customer@example.com",
            }
        ]
        resp = self.client.post(
            "/webhooks/mailjet",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        event = SentEmailEvent.objects.get()
        self.assertEqual(event.event_type, "open")
        self.assertEqual(event.sent_email_id, self.sent.id)
        self.assertEqual(event.message_uuid, self.sent.message_uuid)
        self.assertEqual(
            event.timestamp,
            datetime.fromtimestamp(1433103519, tz=dt_timezone.utc),
        )

    def test_unmatched_uuid_still_stored(self):
        payload = {
            "event": "bounce",
            "time": 1430812195,
            "Message_GUID": "does-not-exist",
            "email": "bounce@example.com",
        }
        resp = self.client.post(
            "/webhooks/mailjet",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        event = SentEmailEvent.objects.get()
        self.assertIsNone(event.sent_email)
        self.assertEqual(event.event_type, "bounce")
        self.assertEqual(event.message_uuid, "does-not-exist")

    def test_invalid_json_returns_400(self):
        resp = self.client.post(
            "/webhooks/mailjet",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    @override_settings(MAILJET_WEBHOOK_SECRET="s3cret")
    def test_shared_secret_header_required(self):
        payload = [{"event": "sent", "time": 1, "Message_GUID": "x"}]
        missing = self.client.post(
            "/webhooks/mailjet",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(missing.status_code, 401)

        ok = self.client.post(
            "/webhooks/mailjet",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_MAILJET_WEBHOOK_SECRET="s3cret",
        )
        self.assertEqual(ok.status_code, 200)

        ok_query = self.client.post(
            "/webhooks/mailjet?secret=s3cret",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(ok_query.status_code, 200)




@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    MAILJET_WEBHOOK_SECRET="expected-secret",
    DEBUG=False,
)
class MailjetWebhookAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_rejects_when_secret_configured_and_missing(self):
        resp = self.client.post(
            "/webhooks/mailjet",
            data=json.dumps({"event": "open"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_accepts_matching_query_secret(self):
        resp = self.client.post(
            "/webhooks/mailjet?secret=expected-secret",
            data=json.dumps({"event": "click", "email": "a@b.com"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SentEmailEvent.objects.count(), 1)

    def test_rejects_when_secret_unset_and_not_debug(self):
        with override_settings(MAILJET_WEBHOOK_SECRET=None, DEBUG=False):
            resp = self.client.post(
                "/webhooks/mailjet",
                data=json.dumps({"event": "bounce"}),
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, 401)
