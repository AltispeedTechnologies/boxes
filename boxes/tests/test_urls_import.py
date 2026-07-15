"""Ensure urls import without exec and named app routes reverse."""
from django.test import SimpleTestCase
from django.urls import reverse, NoReverseMatch


class UrlsImportTests(SimpleTestCase):
    def test_urlpatterns_importable(self):
        from boxes.urls import urlpatterns
        self.assertGreater(len(urlpatterns), 10)

    def test_named_routes_reverse(self):
        samples = [
            ("home", {}),
            ("login", {}),
            ("packages", {}),
            ("check_in", {}),
            ("customer_parcels", {}),
            ("mailjet_webhooks", {}),
            ("stripe_totals", {}),
            ("pickup_mgmt", {}),
            ("session_set_active_account", {}),
            ("account_members_link", {"pk": 1}),
            ("account_fee_waiver", {"pk": 1}),
        ]
        for name, kwargs in samples:
            try:
                url = reverse(name, kwargs=kwargs)
            except NoReverseMatch as exc:
                self.fail(f"reverse({name!r}) failed: {exc}")
            self.assertTrue(url.startswith("/"))
