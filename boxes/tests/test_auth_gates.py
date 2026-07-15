"""URL access control matrix for anonymous, customer, staff, delivery."""
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.tests.helpers import make_user


@override_settings(ALLOWED_HOSTS=["*"], SECURE_SSL_REDIRECT=False)
class AuthGateTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        Group.objects.get_or_create(name="Delivery")
        self.staff = make_user(username="gate_staff", groups=["Staff"])
        self.customer = make_user(username="gate_customer", groups=["Customer"])
        self.delivery = make_user(username="gate_delivery", groups=["Delivery"])

    def test_anonymous_staff_route_redirects_login(self):
        r = self.client.get("/mgmt/general")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r["Location"])

    def test_customer_forbidden_on_staff_mgmt(self):
        self.client.force_login(self.customer)
        r = self.client.get("/mgmt/general")
        self.assertEqual(r.status_code, 403)

    def test_staff_can_access_mgmt(self):
        self.client.force_login(self.staff)
        r = self.client.get("/mgmt/general")
        self.assertEqual(r.status_code, 200)

    def test_delivery_can_checkin_not_mgmt(self):
        self.client.force_login(self.delivery)
        r = self.client.get("/packages/checkin")
        self.assertEqual(r.status_code, 200)
        r2 = self.client.get("/mgmt/general")
        self.assertEqual(r2.status_code, 403)

    def test_customer_can_parcels_staff_cannot_customer_payments_as_forbidden_if_not_customer(self):
        self.client.force_login(self.customer)
        r = self.client.get("/customer/parcels")
        self.assertIn(r.status_code, (200, 302))  # may redirect to select account
        self.client.force_login(self.staff)
        r2 = self.client.get("/customer/payments")
        self.assertEqual(r2.status_code, 403)
