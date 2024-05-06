from django.db import models

class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    content = models.TextField()

class EmailSettings(models.Model):
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    check_in_template = models.ForeignKey(EmailTemplate, related_name="check_in_templates", on_delete=models.SET_NULL, null=True)

class NotificationRule(models.Model):
    email_settings = models.ForeignKey(EmailSettings, related_name="notification_rules", on_delete=models.CASCADE)
    days = models.IntegerField()
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
