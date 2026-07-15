"""Tests for GlobalSettings.load()."""
from django.test import TestCase, override_settings

from boxes.models import GlobalSettings


@override_settings(ALLOWED_HOSTS=["*"])
class GlobalSettingsTests(TestCase):
    def test_load_creates_when_empty(self):
        GlobalSettings.objects.all().delete()
        gs = GlobalSettings.load()
        self.assertIsNotNone(gs.pk)
        self.assertEqual(GlobalSettings.objects.count(), 1)
        self.assertEqual(GlobalSettings.load().pk, gs.pk)
