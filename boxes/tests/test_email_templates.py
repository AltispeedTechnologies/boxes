"""Tests for email template substitution and staff template pages."""
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings

from boxes.models import EmailTemplate
from boxes.tasks.emails import _prepare_email_content
from boxes.tests.helpers import make_user
from boxes.views.common import _clean_html


class PrepareEmailContentTests(TestCase):
    """Token substitution, braces safety, and plain-text conversion."""

    def setUp(self):
        self.user = make_user(
            username="mailuser",
            first_name="Jane",
            last_name="Doe",
        )

    def _template(self, content, subject="Package for {first_name}"):
        return EmailTemplate.objects.create(
            name="Test template",
            subject=subject,
            content=content,
        )

    def test_all_tokens_via_data_token_chips(self):
        content = (
            '<p>'
            '<span contenteditable="false" class="custom-block" data-token="first_name">First Name</span> '
            '<span contenteditable="false" class="custom-block" data-token="last_name">Last Name</span> '
            '<span contenteditable="false" class="custom-block" data-token="full_name">Full Name</span> '
            '<span contenteditable="false" class="custom-block" data-token="tracking_code">Tracking Code</span> '
            '<span contenteditable="false" class="custom-block" data-token="carrier">Carrier</span> '
            '<span contenteditable="false" class="custom-block" data-token="comment">Comment</span>'
            "</p>"
        )
        template = self._template(content, subject="Hi {full_name}")
        hr_name, email_html, email_text, subject = _prepare_email_content(
            self.user, template, "TRK123", "UPS", "Leave at door"
        )
        self.assertEqual(hr_name, "Jane Doe")
        self.assertEqual(subject, "Hi Jane Doe")
        self.assertIn("Jane", email_html)
        self.assertIn("Doe", email_html)
        self.assertIn("Jane Doe", email_html)
        self.assertIn("TRK123", email_html)
        self.assertIn("UPS", email_html)
        self.assertIn("Leave at door", email_html)
        self.assertNotIn("data-token", email_html)
        self.assertNotIn("{first_name}", email_html)
        self.assertIn("Jane", email_text)
        self.assertIn("TRK123", email_text)

    def test_all_tokens_via_brace_placeholders(self):
        content = (
            "<p>{first_name}|{last_name}|{full_name}|{tracking_code}|{carrier}|{comment}</p>"
        )
        template = self._template(content, subject="{first_name} / {tracking_code}")
        _, email_html, _, subject = _prepare_email_content(
            self.user, template, "ABC", "USPS", "note"
        )
        self.assertEqual(subject, "Jane / ABC")
        self.assertEqual(
            email_html,
            "<p>Jane|Doe|Jane Doe|ABC|USPS|note</p>",
        )

    def test_legacy_custom_block_chips(self):
        content = (
            '<span class="custom-block bg-light mx-1 p-2">First Name</span> '
            '<span class="custom-block">Tracking Code</span>'
        )
        template = self._template(content)
        _, email_html, _, _ = _prepare_email_content(
            self.user, template, "Z9", "FedEx", ""
        )
        self.assertIn("Jane", email_html)
        self.assertIn("Z9", email_html)
        self.assertNotIn("First Name", email_html)
        self.assertNotIn("Tracking Code", email_html)

    def test_braces_in_css_are_safe(self):
        """Literal braces outside known tokens must not raise or corrupt content."""
        content = (
            '<p style="font-family: {unknown_font}">Hello {first_name} '
            "{not_a_token} {{double}}</p>"
        )
        template = self._template(content, subject="Use {fake} and {first_name}")
        _, email_html, _, subject = _prepare_email_content(
            self.user, template, "T", "C", "X"
        )
        self.assertIn("Hello Jane", email_html)
        self.assertIn("{unknown_font}", email_html)
        self.assertIn("{not_a_token}", email_html)
        self.assertIn("{{double}}", email_html)
        self.assertEqual(subject, "Use {fake} and Jane")

    def test_subject_and_body_both_substituted(self):
        template = self._template(
            "<p>Body {last_name}</p>",
            subject="Subj {first_name} {tracking_code}",
        )
        _, email_html, _, subject = _prepare_email_content(
            self.user, template, "TK", "CarrierX", "c"
        )
        self.assertEqual(subject, "Subj Jane TK")
        self.assertEqual(email_html, "<p>Body Doe</p>")

    def test_plaintext_converts_br_and_p_before_strip(self):
        content = "<p>Line one</p><p>Line two</p>Line three<br>Line four<br/>End"
        template = self._template(content)
        _, _, email_text, _ = _prepare_email_content(
            self.user, template, "t", "c", "n"
        )
        # Newlines where br/p were; no raw tags
        self.assertNotIn("<", email_text)
        self.assertNotIn(">", email_text)
        self.assertIn("Line one", email_text)
        self.assertIn("Line two", email_text)
        self.assertIn("Line three", email_text)
        self.assertIn("Line four", email_text)
        self.assertIn("\n", email_text)
        # Order preserved with separators
        one_idx = email_text.index("Line one")
        two_idx = email_text.index("Line two")
        three_idx = email_text.index("Line three")
        four_idx = email_text.index("Line four")
        self.assertLess(one_idx, two_idx)
        self.assertLess(two_idx, three_idx)
        self.assertLess(three_idx, four_idx)
        # At least one newline between paragraphs / breaks
        self.assertIn("Line one\n", email_text)
        self.assertIn("Line three\nLine four", email_text)

    def test_clean_html_preserves_data_token(self):
        html = (
            '<span contenteditable="false" style="user-select: none;" '
            'class="custom-block bg-light mx-1 p-2" data-token="first_name">'
            "First Name</span>"
        )
        cleaned = _clean_html(html)
        self.assertIn('data-token="first_name"', cleaned)
        self.assertIn("custom-block", cleaned)


@override_settings(
    ALLOWED_HOSTS=["*"],
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class EmailTemplateViewTests(TestCase):
    """Staff email template management endpoints."""

    def setUp(self):
        Group.objects.get_or_create(name="Staff")
        Group.objects.get_or_create(name="Customer")
        self.staff = make_user(username="staff_email", groups=["Staff", "Customer"])
        self.client = Client()
        self.client.force_login(self.staff)

    def test_empty_template_list_get_returns_200(self):
        self.assertEqual(EmailTemplate.objects.count(), 0)
        response = self.client.get("/mgmt/email/templates")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configure Email Templates")

    def test_fetch_without_id_does_not_500(self):
        response = self.client.get("/mgmt/email/templates/fetch")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get("success", True))

    def test_fetch_and_update_round_trip(self):
        template = EmailTemplate.objects.create(
            name="Check-in",
            subject="Hello",
            content="<p>Hi</p>",
        )
        fetch = self.client.get("/mgmt/email/templates/fetch", {"id": template.id})
        self.assertEqual(fetch.status_code, 200)
        self.assertTrue(fetch.json()["success"])
        self.assertEqual(fetch.json()["subject"], "Hello")

        chip = (
            '<span contenteditable="false" class="custom-block" '
            'data-token="first_name">First Name</span>'
        )
        update = self.client.post(
            "/mgmt/email/templates/update",
            {
                "id": template.id,
                "subject": "Hi {first_name}",
                "content": f"<p>Welcome {chip}</p>",
            },
        )
        self.assertEqual(update.status_code, 200)
        self.assertTrue(update.json().get("success"))
        template.refresh_from_db()
        self.assertEqual(template.subject, "Hi {first_name}")
        self.assertIn('data-token="first_name"', template.content)

    def test_add_template(self):
        response = self.client.post(
            "/mgmt/email/templates/add",
            {"name": "Reminder"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(EmailTemplate.objects.filter(pk=data["id"], name="Reminder").exists())
