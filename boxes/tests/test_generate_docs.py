"""Smoke test for generate_docs management command."""
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase


class GenerateDocsTests(SimpleTestCase):
    def test_generate_docs_writes_files(self):
        call_command("generate_docs")
        api = Path("docs/api")
        self.assertTrue(api.exists())
        files = list(api.glob("*.md"))
        self.assertGreater(len(files), 0)
