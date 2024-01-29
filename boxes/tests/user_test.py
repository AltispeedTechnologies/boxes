from django.contrib.auth.models import Group, Permission, ContentType
from django.test import TestCase
from boxes.models import *

class CustomUserTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpassword",
            company="Test Company",
            prefix="Mr.",
            middle_name="John",
            suffix="Jr.",
            comments="This is a test user."
        )
        self.group = Group.objects.create(name="Test Group")
        content_type, created = ContentType.objects.get_or_create(app_label="boxes", model="customuser")
        self.permission = Permission.objects.create(name="Test Permission", codename="test_permission", content_type=content_type)

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpassword"))
        self.assertEqual(self.user.company, "Test Company")
        self.assertEqual(self.user.prefix, "Mr.")
        self.assertEqual(self.user.middle_name, "John")
        self.assertEqual(self.user.suffix, "Jr.")
        self.assertEqual(self.user.comments, "This is a test user.")

    def test_user_groups_and_permissions(self):
        self.user.groups.add(self.group)
        self.user.user_permissions.add(self.permission)

        self.assertIn(self.group, self.user.groups.all())
        self.assertIn(self.permission, self.user.user_permissions.all())
