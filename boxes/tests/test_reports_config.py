"""Tests for report clean_config and relative_date_range / chart helpers."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from boxes.backend import reports as reports_backend
from boxes.models import PackageLedger, Report, SentEmail, SentEmailEvent, SentEmailPackage
from boxes.tests.helpers import make_account, make_carrier, make_package, make_user


def _base_config(**overrides):
    cfg = {
        "fields": ["tracking_code", "status"],
        "sort_by": "tracking_code",
        "filter": {"type": "all"},
        "state": "all",
    }
    cfg.update(overrides)
    return cfg


class CleanConfigTests(TestCase):
    def test_accepts_email_status_field(self):
        cfg = _base_config(fields=["tracking_code", "email_status"], sort_by="email_status")
        self.assertTrue(reports_backend.clean_config(cfg))

    def test_rejects_unknown_field(self):
        cfg = _base_config(fields=["not_a_field"])
        self.assertFalse(reports_backend.clean_config(cfg))

    def test_relative_open_ended_start_only(self):
        cfg = _base_config(filter={"type": "relative_date_range", "start": 180})
        self.assertTrue(reports_backend.clean_config(cfg))

    def test_relative_closed_range(self):
        cfg = _base_config(filter={"type": "relative_date_range", "start": 0, "end": 180})
        self.assertTrue(reports_backend.clean_config(cfg))

    def test_relative_rejects_end_not_greater(self):
        cfg = _base_config(filter={"type": "relative_date_range", "start": 30, "end": 7})
        self.assertFalse(reports_backend.clean_config(cfg))

    def test_relative_rejects_negative_start(self):
        cfg = _base_config(filter={"type": "relative_date_range", "start": -1})
        self.assertFalse(reports_backend.clean_config(cfg))


class RelativeDateRangeReportTests(TestCase):
    def setUp(self):
        self.user = make_user(username="rptuser")
        self.account = make_account(user=self.user)
        self.now = timezone.now()

        self.old_pkg = make_package(self.account, tracking_code="OLD00001")
        self.new_pkg = make_package(self.account, tracking_code="NEW00001")

        old_ledger = PackageLedger.objects.create(
            user=self.user, package=self.old_pkg, state=1
        )
        new_ledger = PackageLedger.objects.create(
            user=self.user, package=self.new_pkg, state=1
        )
        # Force timestamps (auto_now_add) via update
        PackageLedger.objects.filter(pk=old_ledger.pk).update(
            timestamp=self.now - timedelta(days=200)
        )
        PackageLedger.objects.filter(pk=new_ledger.pk).update(
            timestamp=self.now - timedelta(days=10)
        )

    def test_open_ended_over_n_days_includes_old_checkins(self):
        report = Report.objects.create(
            name="Over 180",
            config={
                "fields": ["tracking_code"],
                "sort_by": "tracking_code",
                "filter": {"type": "relative_date_range", "start": 180},
                "state": "all",
            },
        )
        _, headers, query = reports_backend.generate_full_report(report.pk)
        codes = {row["tracking_code"] for row in query}
        self.assertIn("OLD00001", codes)
        self.assertNotIn("NEW00001", codes)


class PackagesByCarrierByDayTests(TestCase):
    def setUp(self):
        self.user = make_user(username="chartuser")
        self.account = make_account(user=self.user)
        ups = make_carrier("UPS")
        fedex = make_carrier("FedEx")
        p1 = make_package(self.account, carrier=ups, tracking_code="UPS1")
        p2 = make_package(self.account, carrier=fedex, tracking_code="FDX1")
        for pkg in (p1, p2):
            PackageLedger.objects.create(user=self.user, package=pkg, state=1)

    def test_groups_checkins_by_carrier(self):
        data = reports_backend.packages_by_carrier_by_day("Y")
        self.assertIn("x_data", data)
        self.assertIn("y_data", data)
        self.assertIn("UPS", data["y_data"])
        self.assertIn("FedEx", data["y_data"])
        self.assertEqual(sum(data["y_data"]["UPS"]), 1)
        self.assertEqual(sum(data["y_data"]["FedEx"]), 1)

    def test_chart_generate_includes_packages_by_carrier(self):
        chart_data, total_data = reports_backend.report_chart_generate("W")
        self.assertIn("packages_by_carrier", chart_data)
        self.assertIn("y_data", chart_data["packages_by_carrier"])
