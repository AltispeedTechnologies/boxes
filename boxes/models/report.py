from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField()


class ReportResult(models.Model):
    report = models.OneToOneField(Report, on_delete=models.RESTRICT)
    pdf_path = models.CharField(max_length=512, blank=True, null=True)
    last_success = models.DateTimeField(null=True)

    # 0: Not generated ever
    # 1: Queued
    # 2: In Progress
    # 3: Completed Successfully
    # 4: Failed
    status = models.IntegerField(default=0)

    # Progress bar value
    progress = models.IntegerField(default=0)
