"""Email templates, settings, queue, and sent-mail audit trail."""
from django.db import models
from django.utils import timezone


class EmailTemplate(models.Model):
    """Reusable subject/body template for notifications."""
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    content = models.TextField()


class EmailSettings(models.Model):
    """Sender identity and default check-in template (singleton-style)."""
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    check_in_template = models.ForeignKey(EmailTemplate, related_name="check_in_templates", on_delete=models.SET_NULL,
                                          null=True)


class NotificationRule(models.Model):
    """After ``days`` days, enqueue ``template`` for matching packages."""
    email_settings = models.ForeignKey(EmailSettings, related_name="notification_rules", on_delete=models.CASCADE)
    days = models.IntegerField()
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)


class EmailQueue(models.Model):
    """Pending outbound email work item (package + template)."""
    package = models.ForeignKey("Package", on_delete=models.CASCADE)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)


class SentEmail(models.Model):
    """Audit row for an attempted send (success, Mailjet uuid, recipient).

    ``account`` is set for package notifications; signup invites may omit it
    when no billing account is linked yet.
    """
    account = models.ForeignKey(
        "Account", on_delete=models.SET_NULL, null=True, blank=True
    )
    subject = models.CharField()
    email = models.CharField()
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField()
    message_uuid = models.CharField(null=True)


class SentEmailContents(models.Model):
    """HTML body snapshot for a sent email."""
    sent_email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    html = models.TextField()


class SentEmailPackage(models.Model):
    """Packages referenced by a sent email."""
    sent_email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    package = models.ForeignKey("Package", on_delete=models.CASCADE)


class SentEmailResult(models.Model):
    """Raw provider response JSON for a send attempt."""
    sent_email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    response = models.JSONField()


class SentEmailEvent(models.Model):
    """Mailjet delivery event (sent/open/click/bounce/etc.) for a sent message.

    Linked to SentEmail when Message_GUID matches ``message_uuid``; unmatched
    events are still stored for later reconciliation.
    """
    sent_email = models.ForeignKey(
        SentEmail, on_delete=models.CASCADE, null=True, blank=True, related_name="events"
    )
    event_type = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    message_uuid = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["message_uuid", "event_type"]),
        ]
