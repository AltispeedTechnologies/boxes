"""Tests for pickup schedule expansion, inactive overrides, and reservations."""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.backend.pickup import (
    expand_schedule_rule,
    expand_schedule_rules,
    get_or_create_open_pickup_day,
    list_open_pickup_dates,
    set_pickup_day_active,
)
from boxes.models import (
    PackagePickupReservation,
    PickupDay,
    PickupScheduleRule,
)
from boxes.tests.helpers import link_user, make_account, make_package, make_user


class ScheduleExpansionTests(TestCase):
    def test_weekly_rule_expands_matching_weekdays(self):
        rule = PickupScheduleRule(
            name="Mondays",
            recurrence=PickupScheduleRule.RECURRENCE_WEEKLY,
            weekday=0,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            is_active=True,
        )
        dates = expand_schedule_rule(rule, date(2026, 7, 1), date(2026, 7, 31))
        self.assertEqual(
            sorted(dates),
            [
                date(2026, 7, 6),
                date(2026, 7, 13),
                date(2026, 7, 20),
                date(2026, 7, 27),
            ],
        )

    def test_none_recurrence_is_single_day(self):
        rule = PickupScheduleRule(
            name="Once",
            recurrence=PickupScheduleRule.RECURRENCE_NONE,
            start_date=date(2026, 8, 5),
            is_active=True,
        )
        self.assertEqual(
            expand_schedule_rule(rule, date(2026, 8, 1), date(2026, 8, 31)),
            {date(2026, 8, 5)},
        )
        self.assertEqual(
            expand_schedule_rule(rule, date(2026, 9, 1), date(2026, 9, 30)),
            set(),
        )

    def test_inactive_rule_yields_nothing(self):
        rule = PickupScheduleRule(
            name="Off",
            recurrence=PickupScheduleRule.RECURRENCE_WEEKLY,
            weekday=2,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            is_active=False,
        )
        self.assertEqual(
            expand_schedule_rule(rule, date(2026, 7, 1), date(2026, 7, 31)),
            set(),
        )

    def test_expand_schedule_rules_unions_active_db_rules(self):
        PickupScheduleRule.objects.create(
            name="Mon",
            recurrence=PickupScheduleRule.RECURRENCE_WEEKLY,
            weekday=0,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 14),
            is_active=True,
        )
        PickupScheduleRule.objects.create(
            name="Once",
            recurrence=PickupScheduleRule.RECURRENCE_NONE,
            start_date=date(2026, 7, 10),
            is_active=True,
        )
        dates = expand_schedule_rules(date(2026, 7, 1), date(2026, 7, 14))
        self.assertIn(date(2026, 7, 6), dates)
        self.assertIn(date(2026, 7, 13), dates)
        self.assertIn(date(2026, 7, 10), dates)


class InactiveOverrideTests(TestCase):
    def test_inactive_pickup_day_removes_rule_date(self):
        PickupScheduleRule.objects.create(
            name="Mon",
            recurrence=PickupScheduleRule.RECURRENCE_WEEKLY,
            weekday=0,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            is_active=True,
        )
        # 2026-07-13 is a Monday from the rule
        PickupDay.objects.create(date=date(2026, 7, 13), is_active=False)
        open_dates = list_open_pickup_dates(date(2026, 7, 1), date(2026, 7, 31))
        self.assertNotIn(date(2026, 7, 13), open_dates)
        self.assertIn(date(2026, 7, 6), open_dates)

    def test_active_one_off_day_added_without_rule(self):
        PickupDay.objects.create(date=date(2026, 7, 4), is_active=True)
        open_dates = list_open_pickup_dates(date(2026, 7, 1), date(2026, 7, 10))
        self.assertEqual(open_dates, [date(2026, 7, 4)])

    def test_get_or_create_open_pickup_day_rejects_closed(self):
        PickupDay.objects.create(date=date(2026, 7, 4), is_active=False)
        with self.assertRaises(ValueError):
            get_or_create_open_pickup_day(date(2026, 7, 4))


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class ReservationCreateTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.customer = make_user(username="cust1", groups=["Customer"])
        self.account = make_account(user=self.customer, balance=Decimal("0.00"))
        link_user(self.customer, self.account)
        self.package = make_package(
            self.account, price=Decimal("6.00"), current_state=1
        )
        self.client = Client()
        self.client.force_login(self.customer)
        # Open a concrete day inside the customer open-window (today .. +60d)
        self.open_date = date.today() + timedelta(days=7)
        self.day = PickupDay.objects.create(date=self.open_date, is_active=True)
        self.open_date_str = self.open_date.isoformat()

    def test_create_reservation_via_helper(self):
        day = get_or_create_open_pickup_day(self.open_date)
        res = PackagePickupReservation.objects.create(
            package=self.package,
            pickup_day=day,
            user=self.customer,
        )
        self.assertEqual(res.pickup_day.date, self.open_date)
        self.assertEqual(self.package.pickup_reservation.pickup_day_id, day.id)

    def test_customer_reserve_endpoint(self):
        response = self.client.post(
            "/customer/parcels/reserve",
            data='{"package_ids": [%d], "date": "%s"}' % (self.package.id, self.open_date_str),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertEqual(payload["created"], 1)
        self.assertTrue(
            PackagePickupReservation.objects.filter(
                package=self.package, pickup_day=self.day
            ).exists()
        )

    def test_reserve_rejects_closed_day(self):
        self.day.is_active = False
        self.day.save()
        response = self.client.post(
            "/customer/parcels/reserve",
            data='{"package_ids": [%d], "date": "%s"}' % (self.package.id, self.open_date_str),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload.get("success"))

    @patch("boxes.tasks.pickup.notify_pickup_day_cancelled.delay")
    def test_deactivate_day_with_reservation_enqueues_notify(self, delay_mock):
        PackagePickupReservation.objects.create(
            package=self.package,
            pickup_day=self.day,
            user=self.customer,
        )
        set_pickup_day_active(self.day, False)
        self.day.refresh_from_db()
        self.assertFalse(self.day.is_active)
        delay_mock.assert_called_once_with(self.day.id)

    def test_open_days_endpoint(self):
        response = self.client.get("/customer/pickup/open")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertIn(self.open_date_str, payload.get("dates", []))
