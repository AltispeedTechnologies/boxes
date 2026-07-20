"""API-layer tests for package create (JSON) and search robustness."""
from decimal import Decimal

from django.test import Client, TestCase, override_settings

from boxes.tests.helpers import (
    ensure_group,
    make_account,
    make_carrier,
    make_package_type,
    make_user,
)
from boxes.models import Package, Queue


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class PackageAPITests(TestCase):
    def setUp(self):
        ensure_group("Staff")
        ensure_group("Customer")
        self.staff = make_user(username="pkg_staff", groups=["Staff", "Customer"], is_staff=True)
        self.account = make_account(user=self.staff, name="Pkg Acct")
        self.carrier = make_carrier(name="UPS")
        self.ptype = make_package_type()
        self.queue = Queue.objects.create(description="Q1", check_in=True)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_create_package_json(self):
        response = self.client.post(
            "/packages/checkin/create",
            data=(
                '{"tracking_code": "JSONPKG001", "account_id": %d, "carrier_id": %d,'
                ' "package_type_id": %d, "queue_id": "%d", "price": "6.00", "inside": true}'
            ) % (self.account.id, self.carrier.id, self.ptype.id, self.queue.id),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertTrue(Package.objects.filter(tracking_code="JSONPKG001").exists())

    def test_search_without_filter_param(self):
        response = self.client.get("/packages/search?q=JSON")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"AttributeError", response.content)
