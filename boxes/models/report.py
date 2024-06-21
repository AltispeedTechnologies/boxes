from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField()


class ReportResult(models.Model):
    report = models.OneToOneField(Report, on_delete=models.RESTRICT)
    pdf_path = models.CharField(max_length=512, blank=True, null=True)
    last_success = models.DateTimeField(null=True)

    # 0: Not generated ever
    # 1: In Progress or Queued
    # 2: Completed Successfully
    # 3: Failed
    status = models.IntegerField(default=0)
