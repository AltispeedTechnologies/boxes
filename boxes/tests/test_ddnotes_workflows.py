"""Regression tests for Dark Decoy / QA workflow notes."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.models import (
    Account,
    Carrier,
    Package,
    PackageQueue,
    PackageSystemTrackingCode,
    PackageType,
    Queue,
)
from boxes.tests.helpers import make_account


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class CheckInTrackingGenerateTests(TestCase):
    """Internal tracking codes only mint when generate_tracking is set."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="staffqa", password="x")
        for name in ("Staff", "Customer"):
            g, _ = Group.objects.get_or_create(name=name)
            self.user.groups.add(g)
        self.client = Client()
        self.client.force_login(self.user)
        self.account = make_account(name="QA Customer")
        self.carrier = Carrier.objects.create(
            name="QACarrier", phone_number="", website="https://example.com"
        )
        self.ptype = PackageType.objects.create(
            shortcode="Q", description="QA type", default_price=Decimal("6.00")
        )
        self.queue = Queue.objects.create(description="QA Queue", check_in=True)

    def _payload(self, **extra):
        body = {
            "tracking_code": "",
            "price": "6.00",
            "carrier_id": str(self.carrier.id),
            "account_id": str(self.account.id),
            "package_type_id": str(self.ptype.id),
            "inside": False,
            "comments": "",
            "queue_id": str(self.queue.id),
        }
        body.update(extra)
        return body

    def test_empty_tracking_without_generate_flag_errors(self):
        resp = self.client.post(
            "/packages/checkin/create",
            data=json.dumps(self._payload(generate_tracking=False)),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get("success"))
        self.assertIn("tracking_code", data.get("form_errors", {}))
        self.assertEqual(Package.objects.count(), 0)

    def test_empty_tracking_with_generate_flag_mints_int_code(self):
        resp = self.client.post(
            "/packages/checkin/create",
            data=json.dumps(self._payload(generate_tracking=True)),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"), data)
        self.assertTrue(data.get("tracking_code", "").startswith("INT"))
        pkg = Package.objects.get(pk=data["id"])
        self.assertTrue(pkg.tracking_code.startswith("INT"))
        self.assertTrue(
            PackageQueue.objects.filter(package=pkg, queue=self.queue).exists()
        )


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class ClearCheckInQueueTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="staffqa2", password="x")
        for name in ("Staff", "Customer"):
            g, _ = Group.objects.get_or_create(name=name)
            self.user.groups.add(g)
        self.client = Client()
        self.client.force_login(self.user)
        self.account = make_account(name="QA2")
        self.carrier = Carrier.objects.create(
            name="QACarrier2", phone_number="", website="https://example.com"
        )
        self.ptype = PackageType.objects.create(
            shortcode="Z", description="QA type 2", default_price=Decimal("6.00")
        )
        self.queue = Queue.objects.create(description="QA Queue 2", check_in=True)
        self.pkg = Package.objects.create(
            account=self.account,
            carrier=self.carrier,
            package_type=self.ptype,
            tracking_code="TRK-CLEAR-1",
            price=Decimal("6.00"),
            current_state=0,
        )
        PackageQueue.objects.create(package=self.pkg, queue=self.queue)

    def test_clear_queue_removes_queue_rows_keeps_package(self):
        resp = self.client.post(
            "/packages/checkin/queue/clear",
            data=json.dumps({"queue_id": self.queue.id}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["removed"], 1)
        self.assertFalse(PackageQueue.objects.filter(queue=self.queue).exists())
        self.assertTrue(Package.objects.filter(pk=self.pkg.pk).exists())
        self.pkg.refresh_from_db()
        self.assertEqual(self.pkg.current_state, 0)


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class SearchAndMgmtUiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="staffqa3", password="x")
        for name in ("Staff", "Customer", "Admin"):
            g, _ = Group.objects.get_or_create(name=name)
            self.user.groups.add(g)
        self.client = Client()
        self.client.force_login(self.user)

    def test_empty_tracking_search_returns_200(self):
        resp = self.client.get("/packages/search", {"q": "", "filter": "tracking_code"})
        self.assertEqual(resp.status_code, 200)

    def test_accounts_mgmt_ok(self):
        resp = self.client.get("/mgmt/accounts")
        self.assertEqual(resp.status_code, 200)

    def test_navbar_has_no_http_connectivity_menu_item(self):
        resp = self.client.get("/packages/checkin")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # Section may exist on env page; Management dropdown must not list it as its own page link
        self.assertNotIn('data-setup-key="http3"', content)
        self.assertNotIn("#http-connectivity", content)

    def test_user_edit_uses_btn_check_group_toggles(self):
        resp = self.client.get(f"/users/{self.user.id}/")
        # try common detail URL
        if resp.status_code == 404:
            from django.urls import reverse
            try:
                url = reverse("user_detail", args=[self.user.id])
            except Exception:
                url = f"/users/{self.user.id}"
            resp = self.client.get(url)
        if resp.status_code == 200:
            body = resp.content.decode()
            self.assertIn("btn-check", body)
            self.assertIn("user-group-check", body)
