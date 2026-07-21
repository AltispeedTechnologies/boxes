"""Integration tests for POST /users/new (Create New Customer modal modes)."""
import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from boxes.models import CustomUser, SignupInvite, UserAccount
from boxes.tests.helpers import ensure_group, make_user


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class CreateCustomerModalAPITest(TestCase):
    def setUp(self):
        ensure_group("Customer")
        ensure_group("Staff")
        self.staff = make_user(username="modal_staff", groups=["Staff", "Customer"])
        self.client = Client()
        self.client.force_login(self.staff)

    def post(self, data):
        return self.client.post(
            "/users/new",
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_noop_rejected(self):
        r = self.post({"create_account": False})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["success"])
        self.assertIn("__all__", body.get("form_errors", {}))

    def test_account_only(self):
        r = self.post({"first_name": "Acct", "last_name": "Only", "create_account": True})
        body = r.json()
        self.assertTrue(body["success"], body)
        self.assertIsNotNone(body["account_id"])
        self.assertFalse(body.get("web_account"))

    def test_account_with_credentials(self):
        r = self.post({
            "first_name": "Both",
            "last_name": "Ways",
            "username": "modal_both",
            "password": "changem3-strong!",
            "password2": "changem3-strong!",
            "create_web_account": True,
            "create_account": True,
            "email": "modal_both@example.com",
        })
        body = r.json()
        self.assertTrue(body["success"], body)
        self.assertTrue(body["web_account"])
        user = CustomUser.objects.get(username="modal_both")
        self.assertTrue(user.is_active)
        self.assertTrue(
            UserAccount.objects.filter(
                user=user, account_id=body["account_id"], is_active=True
            ).exists()
        )

    def test_user_only_no_account(self):
        r = self.post({
            "first_name": "Solo",
            "username": "modal_solo",
            "password": "changem3-strong!",
            "password2": "changem3-strong!",
            "create_web_account": True,
            "create_account": False,
        })
        body = r.json()
        self.assertTrue(body["success"], body)
        self.assertIsNone(body.get("account_id"))
        self.assertFalse(UserAccount.objects.filter(user__username="modal_solo").exists())

    @patch("boxes.backend.signup._send_via_mailjet", return_value=False)
    def test_invite_only(self, _mj):
        r = self.post({
            "first_name": "Invitee",
            "email": "modal_invite@example.com",
            "send_invite": True,
            "create_account": False,
        })
        body = r.json()
        self.assertTrue(body["success"], body)
        self.assertTrue(body["invite"])
        self.assertTrue(SignupInvite.objects.filter(email="modal_invite@example.com").exists())
        self.assertFalse(CustomUser.objects.filter(email="modal_invite@example.com").exists())

    def test_invite_requires_email(self):
        r = self.post({"send_invite": True, "create_account": False, "first_name": "X"})
        body = r.json()
        self.assertFalse(body["success"])
        self.assertIn("email", body.get("form_errors", {}))

    def test_credentials_require_password(self):
        r = self.post({
            "first_name": "NoPw",
            "username": "modal_nopw",
            "create_web_account": True,
            "create_account": False,
        })
        body = r.json()
        self.assertFalse(body["success"])
        self.assertTrue(body.get("form_errors", {}).get("password"))

    def test_navbar_no_separate_users_item(self):
        r = self.client.get("/mgmt/accounts")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Accounts and Users")
        self.assertContains(r, 'href="/mgmt/users"')  # tab still OK
        self.assertNotContains(r, 'data-setup-key="users"')

    def test_env_api_keys_on_general(self):
        r = self.client.get("/mgmt/general")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "API keys and environment")
        self.assertContains(r, "STRIPE_API_KEY")
        self.assertContains(r, "MJ_APIKEY_PUBLIC")
        self.assertContains(r, "/etc/boxes.env")


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class SetupStatusEnvKeysTest(TestCase):
    def setUp(self):
        ensure_group("Staff")
        ensure_group("Customer")
        self.staff = make_user(username="env_staff", groups=["Staff", "Customer"])

    def test_env_api_key_status_shape(self):
        from boxes.backend.setup_status import env_api_key_status, invalidate_setup_status_cache

        invalidate_setup_status_cache()
        status = env_api_key_status()
        self.assertIn("checks", status)
        names = {c["name"] for c in status["checks"]}
        self.assertIn("STRIPE_API_KEY", names)
        self.assertIn("MJ_APIKEY_PUBLIC", names)

    def test_setup_status_has_env_keys_not_users(self):
        from boxes.backend.setup_status import compute_setup_status, invalidate_setup_status_cache

        invalidate_setup_status_cache()
        s = compute_setup_status(use_cache=False)
        self.assertIn("env_keys", s["items"])
        self.assertNotIn("users", s["items"])
        self.assertIn("accounts", s["items"])
