"""Tests for system user helpers."""
from django.test import TestCase, override_settings

from boxes.backend.system import SYSTEM_USERNAME, ensure_system_user, get_system_user
from boxes.models import CustomUser


@override_settings(ALLOWED_HOSTS=["*"])
class SystemUserTests(TestCase):
    def test_ensure_system_user_creates_inactive_actor(self):
        user = ensure_system_user()
        self.assertEqual(user.username, SYSTEM_USERNAME)
        self.assertFalse(user.is_active)
        again = ensure_system_user()
        self.assertEqual(user.pk, again.pk)

    def test_get_system_user_prefers_system_username(self):
        ensure_system_user()
        CustomUser.objects.create_superuser("admin", password="x")
        self.assertEqual(get_system_user().username, SYSTEM_USERNAME)
