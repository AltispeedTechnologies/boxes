"""Tests for package catalog is_active, tracking duplicates, labels, fee waiver."""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.models import AccountLedger, Carrier, Package, PackageType, Queue
from boxes.tests.helpers import make_account, make_carrier, make_package, make_package_type, make_user
from boxes.views.labels import _fit_font_size, _split_text_for_width, draw_centered_string
from boxes.views.packages.utility import tracking_code_conflict
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class IsActiveSearchTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.staff = make_user(username="staff_active", groups=["Staff", "Customer"])
        self.client = Client()
        self.client.force_login(self.staff)

        self.active_carrier = make_carrier(name="ActiveCo")
        self.inactive_carrier = Carrier.objects.create(
            name="InactiveCo", phone_number="555", website="https://x.test", is_active=False
        )
        self.active_type = make_package_type(shortcode="A", description="Active Type")
        self.inactive_type = PackageType.objects.create(
            shortcode="I", description="Inactive Type", default_price=Decimal("1.00"), is_active=False
        )

    def test_carrier_search_excludes_inactive(self):
        r = self.client.get("/carriers/search", {"term": "Co"})
        self.assertEqual(r.status_code, 200)
        texts = [row["text"] for row in r.json()["results"]]
        self.assertIn("ActiveCo", texts)
        self.assertNotIn("InactiveCo", texts)

    def test_type_search_excludes_inactive(self):
        r = self.client.get("/types/search", {"term": "Type"})
        self.assertEqual(r.status_code, 200)
        texts = [row["text"] for row in r.json()["results"]]
        self.assertIn("Active Type", texts)
        self.assertNotIn("Inactive Type", texts)

    def test_mgmt_update_saves_is_active(self):
        import json
        r = self.client.post(
            "/mgmt/packages/carriers/update",
            data=json.dumps({
                str(self.active_carrier.id): {
                    "name": self.active_carrier.name,
                    "phone_number": self.active_carrier.phone_number,
                    "website": self.active_carrier.website,
                    "is_active": False,
                    "allow_duplicate_tracking": True,
                }
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.active_carrier.refresh_from_db()
        self.assertFalse(self.active_carrier.is_active)
        self.assertTrue(self.active_carrier.allow_duplicate_tracking)

        r = self.client.post(
            "/mgmt/packages/types/update",
            data=json.dumps({
                str(self.active_type.id): {
                    "shortcode": self.active_type.shortcode,
                    "description": self.active_type.description,
                    "default_price": str(self.active_type.default_price),
                    "is_active": False,
                }
            }),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.active_type.refresh_from_db()
        self.assertFalse(self.active_type.is_active)


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class TrackingDuplicateTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.staff = make_user(username="staff_trk", groups=["Staff", "Customer"])
        self.client = Client()
        self.client.force_login(self.staff)
        self.account = make_account(user=self.staff)
        self.carrier = make_carrier(name="StrictShip")
        self.dup_carrier = Carrier.objects.create(
            name="DupShip",
            phone_number="555",
            website="https://dup.test",
            allow_duplicate_tracking=True,
        )
        self.pkg_type = make_package_type()
        self.queue = Queue.objects.create(description="In", check_in=True)
        make_package(self.account, carrier=self.carrier, package_type=self.pkg_type, tracking_code="SAME123")

    def test_conflict_helper_blocks_when_not_allowed(self):
        msg = tracking_code_conflict(self.carrier, "SAME123")
        self.assertIsNotNone(msg)

    def test_conflict_helper_allows_when_flag_set(self):
        make_package(self.account, carrier=self.dup_carrier, package_type=self.pkg_type, tracking_code="DUP999")
        self.assertIsNone(tracking_code_conflict(self.dup_carrier, "DUP999"))

    def test_create_package_rejects_duplicate(self):
        r = self.client.post("/packages/checkin/create", {
            "tracking_code": "SAME123",
            "price": "6.00",
            "account_id": str(self.account.id),
            "carrier_id": str(self.carrier.id),
            "package_type_id": str(self.pkg_type.id),
            "queue_id": str(self.queue.id),
            "comments": "",
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body.get("success"))
        self.assertIn("tracking_code", body.get("form_errors", {}))

    def test_create_package_allows_duplicate_when_enabled(self):
        make_package(self.account, carrier=self.dup_carrier, package_type=self.pkg_type, tracking_code="DUP111")
        r = self.client.post("/packages/checkin/create", {
            "tracking_code": "DUP111",
            "price": "6.00",
            "account_id": str(self.account.id),
            "carrier_id": str(self.dup_carrier.id),
            "package_type_id": str(self.pkg_type.id),
            "queue_id": str(self.queue.id),
            "comments": "",
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body.get("success"), body)
        self.assertEqual(Package.objects.filter(carrier=self.dup_carrier, tracking_code="DUP111").count(), 2)

    def test_update_package_rejects_duplicate(self):
        other = make_package(
            self.account, carrier=self.carrier, package_type=self.pkg_type, tracking_code="OTHER1"
        )
        import json
        r = self.client.post(
            f"/packages/{other.id}/update",
            data=json.dumps({"tracking_code": "SAME123"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body.get("success"))
        other.refresh_from_db()
        self.assertEqual(other.tracking_code, "OTHER1")


class LabelNameHelperTests(TestCase):
    def test_no_ellipsis_for_long_names(self):
        long_name = "VeryLongLastNameWithoutSpaces"
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=(4 * inch, 6 * inch))
        draw_centered_string(c, 4.8 * inch, long_name, "Helvetica-Bold", 40, 4 * inch, wrap=True)
        c.save()
        # Helpers must not introduce ellipsis truncation
        size = _fit_font_size(long_name, "Helvetica-Bold", 40, 4 * inch - inch, min_font_size=12)
        self.assertLessEqual(size, 40)
        lines = _split_text_for_width(long_name, "Helvetica-Bold", 12, 4 * inch - inch)
        joined = "".join(lines)
        self.assertNotIn("...", joined)
        self.assertEqual(joined, long_name)

    def test_split_prefers_space(self):
        text = "Some Very Long Customer Name"
        lines = _split_text_for_width(text, "Helvetica-Bold", 40, 2 * inch)
        if len(lines) > 1:
            self.assertTrue(all(lines))
            self.assertEqual(" ".join(lines).replace("  ", " "), text)


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class FeeWaiverTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.staff = make_user(username="staff_fee", groups=["Staff", "Customer"])
        self.client = Client()
        self.client.force_login(self.staff)
        self.account = make_account(user=self.staff, balance=Decimal("-10.00"))

    @patch("boxes.tasks.total_accounts.delay")
    def test_fee_waiver_posts_credit(self, delay_mock):
        import json
        r = self.client.post(
            f"/accounts/{self.account.id}/waiver",
            data=json.dumps({"amount": "5.00", "description": "Goodwill credit"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertTrue(body.get("success"), body)
        entry = AccountLedger.objects.get(id=body["ledger_id"])
        self.assertEqual(entry.credit, Decimal("5.00"))
        self.assertEqual(entry.debit, Decimal("0.00"))
        self.assertEqual(entry.description, "Goodwill credit")
        self.assertFalse(entry.is_late)
        self.assertEqual(entry.account_id, self.account.id)
        delay_mock.assert_called()

    def test_fee_waiver_rejects_non_positive(self):
        import json
        r = self.client.post(
            f"/accounts/{self.account.id}/waiver",
            data=json.dumps({"amount": "0"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json().get("success"))
