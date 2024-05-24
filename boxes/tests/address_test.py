from django.test import TestCase
from boxes.models import *


class AddressTest(TestCase):
    def setUp(self):
        # Create a sample CustomUser, some of this may be duplicated
        # This is just the bare minimum to allow the user to be saved
        self.user = CustomUser()
        self.user.save()

        # Create a sample Address, copies of this can be modified within the
        # tests themselves
        self.address = Address()
        self.address.address = "123 Example St"
        self.address.city = "Green Bay"
        self.address.state_province = "WI"
        self.address.postal_code = "54301"
        self.address.country_code = "USA"
        self.address.save()

    def test_basics(self):
        self.assertEqual(self.address.address, "123 Example St")
        self.assertEqual(self.address.city, "Green Bay")
        self.assertEqual(self.address.state_province, "WI")
        self.assertEqual(self.address.postal_code, "54301")
        self.assertEqual(self.address.country_code, "USA")
