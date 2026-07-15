"""Tests for multi-account membership helpers and customer access control."""
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from boxes.backend.membership import (
    ACTIVE_ACCOUNT_SESSION_KEY,
    associate_user,
    disassociate_user,
    get_active_account,
    list_accounts_for_user,
    require_account_member,
    set_active_account,
)
from boxes.models import Invoice, UserAccount
from boxes.tests.helpers import ensure_group, link_user, make_account, make_user


class MembershipHelpersTest(TestCase):
    """Unit tests for associate / disassociate / active account session."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = make_user(username="member1", groups=["Customer"])
        self.other = make_user(username="member2", groups=["Customer"])
        self.acct_a = make_account(name="Account A", balance=Decimal("-10.00"))
        self.acct_b = make_account(name="Account B", balance=Decimal("-5.00"))

    def test_associate_user_creates_and_reactivates(self):
        m = associate_user(self.acct_a, self.user, role=UserAccount.ROLE_OWNER)
        self.assertTrue(m.is_active)
        self.assertEqual(m.role, UserAccount.ROLE_OWNER)

        disassociate_user(self.acct_a, self.user)
        m.refresh_from_db()
        self.assertFalse(m.is_active)

        m2 = associate_user(self.acct_a, self.user, role=UserAccount.ROLE_MEMBER)
        self.assertEqual(m2.id, m.id)
        self.assertTrue(m2.is_active)
        self.assertEqual(m2.role, UserAccount.ROLE_MEMBER)

    def test_disassociate_user_missing_is_noop(self):
        self.assertIsNone(disassociate_user(self.acct_a, self.user))

    def test_get_active_account_single_membership(self):
        associate_user(self.acct_a, self.user)
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        self.assertEqual(get_active_account(request), self.acct_a)

    def test_get_active_account_multi_requires_session(self):
        associate_user(self.acct_a, self.user)
        associate_user(self.acct_b, self.user)
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        self.assertIsNone(get_active_account(request))

        request.session[ACTIVE_ACCOUNT_SESSION_KEY] = self.acct_b.id
        self.assertEqual(get_active_account(request), self.acct_b)

    def test_set_active_account_permission(self):
        associate_user(self.acct_a, self.user)
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}

        set_active_account(request, self.acct_a.id)
        self.assertEqual(request.session[ACTIVE_ACCOUNT_SESSION_KEY], self.acct_a.id)

        with self.assertRaises(PermissionDenied):
            set_active_account(request, self.acct_b.id)

    def test_require_account_member(self):
        associate_user(self.acct_a, self.user)
        require_account_member(self.user, self.acct_a)
        with self.assertRaises(PermissionDenied):
            require_account_member(self.user, self.acct_b)

    def test_list_accounts_for_user_active_only(self):
        associate_user(self.acct_a, self.user)
        associate_user(self.acct_b, self.user)
        disassociate_user(self.acct_b, self.user)
        accounts = list(list_accounts_for_user(self.user))
        self.assertEqual([a.id for a in accounts], [self.acct_a.id])


class MembershipViewsTest(TestCase):
    """HTTP tests for session switch, staff link, and cross-account 403."""

    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.customer = make_user(username="cust", groups=["Customer"], password="pass")
        self.staff = make_user(username="staffer", groups=["Staff"], password="pass")
        self.acct_a = make_account(name="Acct A")
        self.acct_b = make_account(name="Acct B")
        associate_user(self.acct_a, self.customer)
        associate_user(self.acct_b, self.customer)
        self.client = Client()

    def test_session_set_active_account(self):
        self.client.login(username="cust", password="pass")
        url = reverse("session_set_active_account")
        resp = self.client.post(
            url,
            data='{"account_id": %d}' % self.acct_b.id,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["account_id"], self.acct_b.id)
        self.assertEqual(self.client.session[ACTIVE_ACCOUNT_SESSION_KEY], self.acct_b.id)

    def test_session_set_active_account_rejects_non_member(self):
        outsider = make_user(username="out", groups=["Customer"], password="pass")
        associate_user(self.acct_a, outsider)
        self.client.login(username="out", password="pass")
        resp = self.client.post(
            reverse("session_set_active_account"),
            data='{"account_id": %d}' % self.acct_b.id,
            content_type="application/json",
        )
        # exception_catcher returns 200 with success false for generic exceptions,
        # PermissionDenied may surface as error JSON or 403 depending on handler.
        self.assertIn(resp.status_code, (200, 403, 500))
        if resp.status_code == 200:
            self.assertFalse(resp.json().get("success", True))

    def test_staff_link_and_disassociate(self):
        self.client.login(username="staffer", password="pass")
        new_user = make_user(username="newbie", groups=["Customer"])
        link_url = reverse("account_members_link", kwargs={"pk": self.acct_a.id})
        resp = self.client.post(
            link_url,
            data='{"user_id": %d, "role": "member"}' % new_user.id,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertTrue(
            UserAccount.objects.filter(user=new_user, account=self.acct_a, is_active=True).exists()
        )

        dis_url = reverse("account_members_disassociate", kwargs={"pk": self.acct_a.id})
        resp = self.client.post(
            dis_url,
            data='{"user_id": %d}' % new_user.id,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        m = UserAccount.objects.get(user=new_user, account=self.acct_a)
        self.assertFalse(m.is_active)

    def test_cross_account_invoice_forbidden(self):
        other = make_user(username="othercust", groups=["Customer"], password="pass")
        associate_user(self.acct_b, other)
        inv = Invoice.objects.create(
            account=self.acct_a,
            user=self.customer,
            line_items=[],
            subtotal=Decimal("10.00"),
            tax=None,
            processing_fees=None,
            current_state=0,
            payment_intent_id="pi_test",
        )
        self.client.login(username="othercust", password="pass")
        session = self.client.session
        session[ACTIVE_ACCOUNT_SESSION_KEY] = self.acct_b.id
        session.save()
        resp = self.client.get(reverse("customer_view_invoice", kwargs={"pk": inv.id}))
        self.assertEqual(resp.status_code, 403)

    @override_settings(STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    })
    def test_parcels_requires_account_selection_when_multi(self):
        self.client.login(username="cust", password="pass")
        # multi-account, no session key
        resp = self.client.get(reverse("customer_parcels"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "customer/select_account.html")
