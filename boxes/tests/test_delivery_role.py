"""Access control tests for the Delivery limited role."""
from django.test import Client, TestCase, override_settings

from boxes.tests.helpers import make_user

_STATIC_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    STORAGES=_STATIC_STORAGES,
)
class DeliveryRoleAccessTests(TestCase):
    """Delivery can use floor routes; blocked from staff mgmt and payments."""

    def setUp(self):
        self.delivery = make_user(username="delivery1", groups=["Delivery"])
        self.client = Client()
        self.client.force_login(self.delivery)

    def test_can_access_check_in(self):
        response = self.client.get("/packages/checkin")
        self.assertEqual(response.status_code, 200)

    def test_can_access_package_search(self):
        response = self.client.get("/packages/")
        self.assertEqual(response.status_code, 200)

    def test_can_access_picklists(self):
        response = self.client.get("/picklists/")
        self.assertEqual(response.status_code, 200)

    def test_forbidden_mgmt_general(self):
        response = self.client.get("/mgmt/general")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_customer_payment(self):
        response = self.client.get("/customer/payments")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_account_edit(self):
        response = self.client.get("/accounts/1/edit")
        self.assertEqual(response.status_code, 403)

    def test_staff_still_accesses_check_in(self):
        staff = make_user(username="staff_delivery_test", groups=["Staff"])
        client = Client()
        client.force_login(staff)
        response = client.get("/packages/checkin")
        self.assertEqual(response.status_code, 200)
