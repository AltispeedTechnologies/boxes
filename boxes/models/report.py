"""User-defined reports and generation status."""
from django.db import models


class Report(models.Model):
    """Named report definition; ``config`` holds field/filter JSON."""
    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField()


class ReportResult(models.Model):
    """Generation status, progress, and PDF path for a report (1:1)."""
    report = models.OneToOneField(Report, on_delete=models.CASCADE)
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
