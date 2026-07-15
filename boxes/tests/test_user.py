"""Unit tests for CustomUser."""
from django.contrib.auth.models import Group, Permission, ContentType
from django.test import TestCase
from boxes.models import CustomUser


class CustomUserTest(TestCase):
    """TestCase for user creation."""
    def setUp(self):
        """Prepare user test fixtures."""
        self.user = CustomUser.objects.create(
            username="testuser",
            company="Test Company",
            prefix="Mr.",
            middle_name="John",
            suffix="Jr.",
            comments="This is a test user."
        )
        self.user.set_password("testpassword")
        self.user.save()

    def test_user_creation(self):
        """CustomUser can be created with expected defaults."""
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpassword"))
        self.assertEqual(self.user.company, "Test Company")
        self.assertEqual(self.user.prefix, "Mr.")
        self.assertEqual(self.user.middle_name, "John")
        self.assertEqual(self.user.suffix, "Jr.")
        self.assertEqual(self.user.comments, "This is a test user.")
