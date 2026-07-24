"""Tests for membership roles, setup status flags, and customer account scoping."""
import json
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from boxes.backend.membership import (
    associate_user,
    set_membership_role,
)
from boxes.backend.setup_status import (
    compute_setup_status,
    invalidate_setup_status_cache,
)
from boxes.models import (
    Account,
    CustomUser,
    GlobalSettings,
    Package,
    UserAccount,
)
from boxes.tests.helpers import (
    ensure_group,
    link_user,
    make_account,
    make_carrier,
    make_package,
    make_package_type,
    make_user,
)


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class MembershipRoleTests(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="role_staff", groups=["Staff", "Customer"])
        self.account = make_account(user=self.staff, name="Role Co")
        self.owner = make_user(username="role_owner", groups=["Customer"])
        self.member = make_user(username="role_member", groups=["Customer"])
        associate_user(self.account, self.owner, role=UserAccount.ROLE_OWNER)
        associate_user(self.account, self.member, role=UserAccount.ROLE_MEMBER)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_set_role_member_to_owner(self):
        m = set_membership_role(self.account, self.member, "owner")
        self.assertEqual(m.role, UserAccount.ROLE_OWNER)

    def test_cannot_demote_last_owner(self):
        set_membership_role(self.account, self.member, "member")
        with self.assertRaises(ValidationError):
            set_membership_role(self.account, self.owner, "member")

    def test_api_set_role(self):
        r = self.client.post(
            f"/accounts/{self.account.id}/members/role",
            data=json.dumps({"user_id": self.member.id, "role": "owner"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))
        self.member.refresh_from_db()
        m = UserAccount.objects.get(user=self.member, account=self.account)
        self.assertEqual(m.role, "owner")

    def test_user_page_set_role(self):
        r = self.client.post(
            f"/users/{self.member.id}/accounts/role",
            data=json.dumps({"account_id": self.account.id, "role": "owner"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("success"))


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class SetupStatusTests(TestCase):
    def setUp(self):
        ensure_group("Staff")
        ensure_group("Customer")
        self.staff = make_user(username="setup_staff", groups=["Staff", "Customer"])
        invalidate_setup_status_cache()

    def test_compute_setup_status_shape(self):
        s = compute_setup_status(use_cache=False)
        self.assertIn("items", s)
        self.assertIn("general", s["items"])
        self.assertIn("carriers", s["items"])
        self.assertIn("required_incomplete", s)

    def test_api_staff_only(self):
        c = Client()
        r = c.get("/mgmt/setup-status")
        self.assertEqual(r.status_code, 302)
        c.force_login(self.staff)
        r = c.get("/mgmt/setup-status?refresh=1")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body.get("success"))
        self.assertIn("setup", body)

    def test_customer_forbidden_setup_api(self):
        customer = make_user(username="setup_cust", groups=["Customer"])
        c = Client()
        c.force_login(customer)
        r = c.get("/mgmt/setup-status")
        self.assertEqual(r.status_code, 403)

    def test_navbar_includes_warn_when_incomplete(self):
        # Ensure general is incomplete
        gs = GlobalSettings.load()
        gs.name = "Boxes"
        gs.address1 = ""
        gs.email = ""
        gs.phone_number = None
        gs.save()
        invalidate_setup_status_cache()
        c = Client()
        c.force_login(self.staff)
        r = c.get("/mgmt/general")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "mgmt-dropdown-warn")
        self.assertContains(r, "setup-warn-icon")



    def test_banner_issues_not_duplicated_for_stripe(self):
        """Stripe key problems must not appear twice in all_issues."""
        from django.test import override_settings

        with override_settings(
            STRIPE_PUBLISHABLE_KEY="",
            STRIPE_SECRET_KEY="sk_test_abcdefghijklmnopqrstuv",
            STRIPE_WEBHOOK_SECRET="whsec_abcdefghijklmnopqrstuv",
            MJ_APIKEY_PUBLIC="publickeypublickey",
            MJ_APIKEY_PRIVATE="privatekeyprivatekey",
        ):
            invalidate_setup_status_cache()
            s = compute_setup_status(use_cache=False)
        # env_keys has detail; stripe has one summary — not two STRIPE_PUBLISHABLE lines
        stripe_pub_lines = [
            i for i in s["all_issues"] if "STRIPE_PUBLISHABLE_KEY" in i
        ]
        self.assertEqual(len(stripe_pub_lines), 1, s["all_issues"])
        self.assertIn("http3", s["items"])
        self.assertTrue(s["items"]["http3"]["ok"])  # server placeholder; client refines

    def test_http3_item_in_setup_status(self):
        invalidate_setup_status_cache()
        s = compute_setup_status(use_cache=False)
        self.assertIn("http3", s["items"])
        self.assertIn("http3", s["order"])
        self.assertTrue(s.get("http3_client_check"))


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class CustomerAccountIsolationTests(TestCase):
    """Security: customers must not act on other accounts' packages."""

    def setUp(self):
        ensure_group("Customer")
        self.u1 = make_user(username="iso_u1", groups=["Customer"])
        self.u2 = make_user(username="iso_u2", groups=["Customer"])
        self.a1 = make_account(user=self.u1, name="Iso A1")
        self.a2 = make_account(user=self.u2, name="Iso A2")
        link_user(self.u1, self.a1)
        link_user(self.u2, self.a2)
        self.carrier = make_carrier("IsoCarrier")
        self.ptype = make_package_type("I", "Iso")
        self.pkg1 = make_package(self.a1, carrier=self.carrier, package_type=self.ptype, tracking_code="ISO1")
        self.pkg2 = make_package(self.a2, carrier=self.carrier, package_type=self.ptype, tracking_code="ISO2")
        self.client = Client()
        self.client.force_login(self.u1)
        from boxes.backend.membership import ACTIVE_ACCOUNT_SESSION_KEY
        session = self.client.session
        session[ACTIVE_ACCOUNT_SESSION_KEY] = self.a1.id
        session.save()

    def test_cannot_reserve_other_account_package(self):
        from boxes.backend.membership import ACTIVE_ACCOUNT_SESSION_KEY
        session = self.client.session
        session[ACTIVE_ACCOUNT_SESSION_KEY] = self.a1.id
        session.save()
        day = (date.today() + timedelta(days=3)).isoformat()
        r = self.client.post(
            "/customer/parcels/reserve",
            data=json.dumps({"package_ids": [self.pkg2.id], "date": day}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 403, r.content)
        body = r.json()
        self.assertFalse(body.get("success", True))

    def test_cannot_set_active_account_without_membership(self):
        r = self.client.post(
            "/session/account",
            data=json.dumps({"account_id": self.a2.id}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 403, r.content)
        self.assertFalse(r.json().get("success", True))

    def test_staff_user_mgmt_customer_403(self):
        r = self.client.get("/mgmt/users")
        self.assertEqual(r.status_code, 403)
        r2 = self.client.get(f"/users/{self.u2.id}/edit")
        self.assertEqual(r2.status_code, 403)
        r3 = self.client.get(f"/accounts/{self.a2.id}/edit")
        self.assertEqual(r3.status_code, 403)
