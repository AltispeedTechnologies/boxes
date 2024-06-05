from django.contrib.auth.models import Group, Permission, ContentType
from django.test import TestCase
from boxes.models import *


class CustomUserTest(TestCase):
    def setUp(self):
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
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpassword"))
        self.assertEqual(self.user.company, "Test Company")
        self.assertEqual(self.user.prefix, "Mr.")
        self.assertEqual(self.user.middle_name, "John")
        self.assertEqual(self.user.suffix, "Jr.")
        self.assertEqual(self.user.comments, "This is a test user.")
