"""Tests for robust user/account association and web portal account creation."""
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from boxes.backend.account import (
    create_account_with_web_user,
    create_billing_account,
    create_user_from_account,
    create_web_user,
    ensure_account_balance,
    ensure_customer_group,
)
from boxes.backend.membership import associate_user, disassociate_user, search_users
from boxes.models import Account, AccountBalance, CustomUser, CustomUserEmail, UserAccount
from boxes.tests.helpers import ensure_group, link_user, make_account, make_user


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class BackendAccountHelpersTest(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="staff_actor", groups=["Staff", "Customer"])

    def test_create_billing_account_with_balance_and_alias(self):
        account = create_billing_account(actor=self.staff, name="Acme Corp")
        self.assertEqual(account.name, "Acme Corp")
        self.assertTrue(AccountBalance.objects.filter(account=account).exists())
        self.assertTrue(account.accountalias_set.filter(primary=True, alias="Acme Corp").exists())

    def test_create_web_user_and_link(self):
        account = create_billing_account(actor=self.staff, name="Billable Co")
        user, membership = create_web_user(
            username="portal1",
            password="changem3-strong!",
            first_name="Pat",
            last_name="Portal",
            email="pat@example.com",
            account=account,
            role=UserAccount.ROLE_OWNER,
            actor=self.staff,
        )
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("changem3-strong!"))
        self.assertTrue(user.is_customer())
        self.assertEqual(membership.role, UserAccount.ROLE_OWNER)
        self.assertTrue(CustomUserEmail.objects.filter(user=user, email="pat@example.com").exists())

    def test_create_web_user_duplicate_username(self):
        create_web_user(
            username="dupuser",
            password="changem3-strong!",
            first_name="A",
        )
        with self.assertRaises(ValidationError):
            create_web_user(
                username="dupuser",
                password="changem3-strong!",
                first_name="B",
            )

    def test_create_account_with_web_user(self):
        result = create_account_with_web_user(
            actor=self.staff,
            username="combo_user",
            password="changem3-strong!",
            first_name="Combo",
            last_name="User",
            email="combo@example.com",
        )
        self.assertEqual(result["account"].name, "Combo User")
        self.assertEqual(result["membership"].role, UserAccount.ROLE_OWNER)
        self.assertTrue(result["user"].is_customer())

    def test_create_user_from_account_idempotent_single(self):
        account = create_billing_account(actor=self.staff, name="Jane Q Public")
        uid1 = create_user_from_account(account.id)
        uid2 = create_user_from_account(account.id)
        self.assertEqual(uid1, uid2)
        user = CustomUser.objects.get(pk=uid1)
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_customer())

    def test_disassociate_last_owner_blocked(self):
        account = create_billing_account(actor=self.staff, name="Solo Owner")
        user, _ = create_web_user(
            username="solo_owner",
            password="changem3-strong!",
            first_name="Solo",
            account=account,
            role=UserAccount.ROLE_OWNER,
        )
        with self.assertRaises(ValidationError):
            disassociate_user(account, user)
        # Allowed with flag
        m = disassociate_user(account, user, allow_last_owner=True)
        self.assertFalse(m.is_active)

    def test_search_users(self):
        make_user(username="findme_xyz", first_name="Find", last_name="Me")
        hits = list(search_users("findme"))
        self.assertTrue(any(u.username == "findme_xyz" for u in hits))


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class WebAccountAPITest(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="api_staff", groups=["Staff", "Customer"], is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_create_user_legacy_without_web(self):
        response = self.client.post(
            "/users/new",
            data='{"first_name": "Legacy", "last_name": "Cust", "email": "legacy@example.com"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertFalse(payload.get("web_account"))
        account = Account.objects.get(pk=payload["account_id"])
        self.assertEqual(account.name, "Legacy Cust")
        self.assertTrue(AccountBalance.objects.filter(account=account).exists())

    def test_create_user_with_web_account(self):
        response = self.client.post(
            "/users/new",
            data=(
                '{"first_name": "Web", "last_name": "Login", "username": "weblogin1",'
                ' "password": "changem3-strong!", "password2": "changem3-strong!",'
                ' "create_web_account": true, "email": "web@example.com"}'
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertTrue(payload.get("web_account"))
        user = CustomUser.objects.get(username="weblogin1")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("changem3-strong!"))
        self.assertTrue(user.is_customer())

    def test_create_web_account_on_existing_account(self):
        account = create_billing_account(actor=self.staff, name="Existing Co")
        response = self.client.post(
            f"/accounts/{account.id}/members/create",
            data=(
                '{"username": "on_existing", "password": "changem3-strong!",'
                ' "password2": "changem3-strong!", "first_name": "On",'
                ' "last_name": "Existing", "role": "owner"}'
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertTrue(
            UserAccount.objects.filter(
                account=account, user__username="on_existing", is_active=True
            ).exists()
        )

    def test_link_by_username(self):
        account = create_billing_account(actor=self.staff, name="Link Co")
        other = make_user(username="linkable", groups=["Customer"])
        response = self.client.post(
            f"/accounts/{account.id}/members/link",
            data='{"username": "linkable", "role": "member"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertTrue(
            UserAccount.objects.filter(account=account, user=other, is_active=True).exists()
        )

    def test_user_search(self):
        make_user(username="searchable_user", first_name="Searchable")
        response = self.client.get("/users/search?term=searchable")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertTrue(any(r["username"] == "searchable_user" for r in payload["results"]))

    def test_update_account_returns_json(self):
        account = create_billing_account(actor=self.staff, name="Update Me")
        response = self.client.post(
            f"/accounts/{account.id}/update",
            data='{"comments": "hello", "billable": false}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        account.refresh_from_db()
        self.assertEqual(account.comments, "hello")
        self.assertFalse(account.billable)

    def test_disassociate_last_owner_via_api(self):
        account = create_billing_account(actor=self.staff, name="Owner Only")
        user, _ = create_web_user(
            username="only_owner",
            password="changem3-strong!",
            first_name="Only",
            account=account,
            role=UserAccount.ROLE_OWNER,
        )
        response = self.client.post(
            f"/accounts/{account.id}/members/disassociate",
            data='{"user_id": %d}' % user.id,
            content_type="application/json",
        )
        self.assertIn(response.status_code, (200, 400))
        payload = response.json()
        self.assertFalse(payload.get("success"))
