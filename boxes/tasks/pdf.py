import logging
import os
import pytz
import sys
from boxes.models import GlobalSettings, ReportResult
from boxes.backend import reports
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML


# Handler for setting the progress level
class PDFLoggingHandler(logging.Handler):
    def __init__(self, result, level=logging.NOTSET):
        super().__init__(level)
        self.result = result

    def emit(self, record):
        if record.getMessage().startswith("Step"):
            step_number = int(record.getMessage().split(" ")[1])
            new_progress = round(((step_number + 1) / 9) * 100)
            if self.result.progress != new_progress:
                self.result.progress = new_progress
                self.result.save()


# Returns the rendered HTML table given a report ID
def _html_table(pk, timestamp):
    # Grab the full report data
    report_name, report_headers, query = reports.generate_full_report(pk)

    # Get the human-readable timestamp
    current_tz = pytz.timezone("America/Chicago")
    hr_timestamp = timestamp.astimezone(current_tz).strftime("%m/%d/%Y %I:%M:%S %p")

    # Get the logo image path
    globalsettings = GlobalSettings.objects.first()
    logo_path = globalsettings.login_image.path

    html_table = render_to_string("reports/_view_table.html", {"report_headers": report_headers,
                                                               "report_name": report_name,
                                                               "business_name": globalsettings.name,
                                                               "page_obj": query,
                                                               "timestamp": hr_timestamp,
                                                               "rendering_pdf": True,
                                                               "logo_path": f"file://{logo_path}"})

    return html_table


def _gen_and_save_pdf(pk):
    # Grab the current timestamp, this will be used both in the report and when storing the result
    timestamp = timezone.now()
    html_table = _html_table(pk, timestamp)

    # Generate the PDF, *this is expensive*
    pdf = HTML(string=html_table).write_pdf()

    # Craft the new file path
    filename = f'report_{timestamp.strftime("%Y%m%d%H%M%S")}.pdf'
    file_path = os.path.join(settings.SECURE_ROOT, filename)

    # Ensure the final directory exists
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    # Write the PDF to disk
    with open(file_path, "wb") as f:
        f.write(pdf)

    return filename, timestamp


@shared_task
def generate_report_pdf(pk):
    # Generating reports is extremely expensive; only generate one at a time
    acquire_lock = cache.add("generate_report_pdf_lock", "true", (60 * 60))

    if not acquire_lock:
        # Task is currently running, so we queue this instance for later execution
        queued_tasks = cache.get("queued_report_tasks", [])
        queued_tasks.append(pk)
        cache.set("queued_report_tasks", queued_tasks, timeout=None)
        return
    try:
        # Fetch the result for this report or create one
        result, _ = ReportResult.objects.get_or_create(report_id=pk)
        # We are now in progress
        result.status = 2
        result.progress = 11
        result.save()

        logger = logging.getLogger("weasyprint.progress")
        logger.setLevel(logging.DEBUG)
        handler = PDFLoggingHandler(result=result)
        logger.addHandler(handler)

        # Generate the PDF accordingly
        filename, timestamp = _gen_and_save_pdf(pk)

        # Remove the old PDF
        try:
            if result.pdf_path:
                old_path = os.path.join(settings.SECURE_ROOT, result.pdf_path)
                os.remove(old_path)
        except OSError:
            pass

        # Confirm it passed, and set database values accordingly
        result.status = 3
        result.progress = 0
        result.pdf_path = filename
        result.last_success = timestamp
        result.save()
    finally:
        # Release the lock
        cache.delete("generate_report_pdf_lock")

        # Get the next item in the queue and start the report generation (if it exists)
        queued_tasks = cache.get("queued_report_tasks", [])
        if queued_tasks:
            next_pk = queued_tasks.pop(0)
            cache.set("queued_report_tasks", queued_tasks, timeout=None)
            generate_report_pdf.delay(next_pk)
