from django.db import models
from django.utils import timezone


class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    content = models.TextField()


class EmailSettings(models.Model):
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    check_in_template = models.ForeignKey(EmailTemplate, related_name="check_in_templates", on_delete=models.SET_NULL,
                                          null=True)


class NotificationRule(models.Model):
    email_settings = models.ForeignKey(EmailSettings, related_name="notification_rules", on_delete=models.CASCADE)
    days = models.IntegerField()
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)


class EmailQueue(models.Model):
    package = models.ForeignKey("Package", on_delete=models.RESTRICT)
    template = models.ForeignKey(EmailTemplate, on_delete=models.RESTRICT)


class SentEmail(models.Model):
    account = models.ForeignKey("Account", on_delete=models.RESTRICT)
    subject = models.CharField()
    email = models.CharField()
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField()
    message_uuid = models.CharField(null=True)


class SentEmailContents(models.Model):
    sent_email = models.ForeignKey(SentEmail, on_delete=models.RESTRICT)
    html = models.TextField()


class SentEmailPackage(models.Model):
    sent_email = models.ForeignKey(SentEmail, on_delete=models.RESTRICT)
    package = models.ForeignKey("Package", on_delete=models.RESTRICT)


class SentEmailResult(models.Model):
    sent_email = models.ForeignKey(SentEmail, on_delete=models.RESTRICT)
    response = models.JSONField()
