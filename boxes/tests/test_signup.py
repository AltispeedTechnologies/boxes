"""Tests for invite-only signup and user management without accounts."""
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from boxes.backend.account import create_web_user
from boxes.backend.signup import (
    complete_signup,
    create_signup_invite,
    get_valid_invite,
    send_signup_invite_email,
)
from boxes.models import Account, CustomUser, SignupInvite, UserAccount
from boxes.tests.helpers import ensure_group, make_account, make_user


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class SignupInviteBackendTest(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="invite_staff", groups=["Staff", "Customer"])

    def test_create_invite_without_account(self):
        invite = create_signup_invite(
            email="new@example.com",
            actor=self.staff,
            first_name="New",
            last_name="Person",
            create_account=False,
        )
        self.assertIsNone(invite.account_id)
        self.assertTrue(invite.is_usable())
        self.assertEqual(invite.email, "new@example.com")

    def test_create_invite_with_account(self):
        invite = create_signup_invite(
            email="withacct@example.com",
            actor=self.staff,
            first_name="With",
            create_account=True,
            account_name="With Account Co",
        )
        self.assertIsNotNone(invite.account_id)
        self.assertEqual(invite.account.name, "With Account Co")
        # No user yet
        self.assertFalse(
            UserAccount.objects.filter(account=invite.account, is_active=True).exists()
        )

    def test_complete_signup_user_only(self):
        invite = create_signup_invite(
            email="solo@example.com",
            actor=self.staff,
            first_name="Solo",
            create_account=False,
        )
        result = complete_signup(
            token=invite.token,
            username="solo_user",
            password="changem3-strong!",
            password2="changem3-strong!",
        )
        user = result["user"]
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_customer())
        self.assertEqual(user.email, "solo@example.com")
        self.assertIsNone(result["membership"])
        self.assertFalse(UserAccount.objects.filter(user=user).exists())
        invite.refresh_from_db()
        self.assertIsNotNone(invite.used_at)
        self.assertEqual(invite.used_by_id, user.id)

    def test_complete_signup_links_account(self):
        account = make_account(user=self.staff, name="Linked Co")
        invite = create_signup_invite(
            email="linked@example.com",
            actor=self.staff,
            first_name="Linked",
            account=account,
            role=UserAccount.ROLE_OWNER,
        )
        result = complete_signup(
            token=invite.token,
            username="linked_user",
            password="changem3-strong!",
        )
        self.assertTrue(
            UserAccount.objects.filter(
                user=result["user"], account=account, is_active=True, role="owner"
            ).exists()
        )

    def test_invite_token_single_use(self):
        invite = create_signup_invite(email="once@example.com", actor=self.staff, first_name="Once")
        complete_signup(token=invite.token, username="once1", password="changem3-strong!")
        with self.assertRaises(ValidationError):
            complete_signup(token=invite.token, username="once2", password="changem3-strong!")

    def test_expired_invite(self):
        invite = create_signup_invite(email="exp@example.com", actor=self.staff, first_name="Exp")
        SignupInvite.objects.filter(pk=invite.pk).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )
        with self.assertRaises(ValidationError):
            get_valid_invite(invite.token)

    @patch("boxes.backend.signup._send_via_mailjet", return_value=False)
    def test_send_invite_email_django_fallback(self, _mock_mj):
        invite = create_signup_invite(email="mail@example.com", actor=self.staff, first_name="Mail")
        sent = send_signup_invite_email(invite)
        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(invite.token, mail.outbox[0].body)
        invite.refresh_from_db()
        self.assertIsNotNone(invite.email_sent_at)


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)

    def test_invite_url_uses_allowed_hosts(self):
        from boxes.backend.signup import invite_signup_url, create_signup_invite
        from django.test import override_settings
        with override_settings(ALLOWED_HOSTS=["boxes.example.test"], SECURE_SSL_REDIRECT=False):
            inv = create_signup_invite(
                email="urlhost@example.com", actor=self.staff, first_name="U", create_account=False
            )
            url = invite_signup_url(inv)
            self.assertEqual(
                url,
                f"http://boxes.example.test/signup/{inv.token}/",
            )
        with override_settings(ALLOWED_HOSTS=["boxes.example.test"], SECURE_SSL_REDIRECT=True):
            url = invite_signup_url(inv)
            self.assertTrue(url.startswith("https://boxes.example.test/signup/"))


class CreateUserAndMgmtAPITest(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="api_staff2", groups=["Staff", "Customer"], is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_create_user_without_account(self):
        response = self.client.post(
            "/users/new",
            data=(
                '{"first_name": "No", "last_name": "Acct", "username": "noacct1",'
                ' "password": "changem3-strong!", "password2": "changem3-strong!",'
                ' "create_web_account": true, "create_account": false,'
                ' "email": "noacct@example.com"}'
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertIsNone(payload.get("account_id"))
        user = CustomUser.objects.get(username="noacct1")
        self.assertTrue(user.is_customer())
        self.assertFalse(UserAccount.objects.filter(user=user).exists())

    @patch("boxes.backend.signup._send_via_mailjet", return_value=False)
    def test_create_user_send_invite(self, _mock_mj):
        response = self.client.post(
            "/users/new",
            data=(
                '{"first_name": "Inv", "last_name": "Itee", "email": "invitee@example.com",'
                ' "send_invite": true, "create_account": false}'
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertTrue(payload.get("invite"))
        self.assertTrue(SignupInvite.objects.filter(email="invitee@example.com").exists())
        self.assertFalse(CustomUser.objects.filter(email="invitee@example.com").exists())

    def test_legacy_create_still_makes_account(self):
        response = self.client.post(
            "/users/new",
            data='{"first_name": "Legacy", "last_name": "Still"}',
            content_type="application/json",
        )
        payload = response.json()
        self.assertTrue(payload.get("success"), payload)
        self.assertIsNotNone(payload.get("account_id"))
        self.assertTrue(Account.objects.filter(pk=payload["account_id"]).exists())

    def test_user_mgmt_page(self):
        make_user(username="listed_user", groups=["Customer"])
        response = self.client.get("/mgmt/users")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "listed_user")

    def test_user_detail_and_link_account(self):
        user, _ = create_web_user(
            username="linkme",
            password="changem3-strong!",
            first_name="Link",
        )
        account = make_account(user=self.staff, name="To Link")
        response = self.client.get(f"/users/{user.id}/edit")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "linkme")

        link = self.client.post(
            f"/users/{user.id}/accounts/link",
            data='{"account_id": %d, "role": "member"}' % account.id,
            content_type="application/json",
        )
        self.assertEqual(link.status_code, 200)
        self.assertTrue(link.json().get("success"))
        self.assertTrue(
            UserAccount.objects.filter(user=user, account=account, is_active=True).exists()
        )

    def test_signup_page_and_register(self):
        invite = create_signup_invite(
            email="selfreg@example.com",
            actor=self.staff,
            first_name="Self",
            create_account=False,
        )
        client = Client()
        get = client.get(f"/signup/{invite.token}/")
        self.assertEqual(get.status_code, 200)
        self.assertContains(get, "selfreg@example.com")

        post = client.post(
            f"/signup/{invite.token}/",
            data={
                "username": "selfreg1",
                "first_name": "Self",
                "last_name": "Reg",
                "password1": "changem3-strong!",
                "password2": "changem3-strong!",
            },
        )
        self.assertEqual(post.status_code, 302)
        user = CustomUser.objects.get(username="selfreg1")
        self.assertTrue(user.is_active)
        # Reuse blocked
        bad = client.get(f"/signup/{invite.token}/")
        self.assertEqual(bad.status_code, 400)

    def test_open_registration_not_available(self):
        client = Client()
        # No bare /register/ or /signup/ without token
        self.assertEqual(client.get("/signup/").status_code, 404)
        self.assertIn(client.get("/register/").status_code, (404, 301, 302))

    def test_invalid_token_signup(self):
        client = Client()
        response = client.get("/signup/not-a-real-token-value/")
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invitation unavailable", status_code=400)
