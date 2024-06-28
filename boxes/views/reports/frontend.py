import csv
import io
import json
import os
from boxes.models import Chart, GlobalSettings, Report, ReportResult
from boxes.backend import reports as reports_backend
from django.conf import settings
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.utils import timezone


@require_http_methods(["GET"])
def report_data(request):
    # The initial filter value is week, get that data
    chart = Chart.objects.filter(frequency="W").first()
    chart_data = json.dumps(chart.chart_data)
    total_data = chart.total_data

    return render(request, "reports/data.html", {"chart_data": chart_data,
                                                 "last_updated": chart.last_updated,
                                                 "total_data": total_data})


@require_http_methods(["GET"])
def report_list(request):
    reports = Report.objects.values("id", "name")

    return render(request, "reports/list.html", {"reports": reports})


@require_http_methods(["GET"])
def report_details(request, pk=None):
    if pk:
        report = Report.objects.filter(pk=pk).first()
        return render(request, "reports/details.html", {"report_config": report.config,
                                                        "report_name": report.name,
                                                        "report_id": report.id})
    else:
        return render(request, "reports/details.html")


@require_http_methods(["GET"])
def report_view(request, pk):
    report_name, report_headers, query = reports_backend.generate_full_report(pk)

    # Pagination
    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(query, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, "reports/view.html", {"report_name": report_name,
                                                 "report_headers": report_headers,
                                                 "report_id": pk,
                                                 "page_obj": page_obj,
                                                 "per_page": per_page})


@require_http_methods(["GET"])
def report_view_pdf(request, pk):
    result, _ = ReportResult.objects.get_or_create(report_id=pk)
    filename = result.pdf_path
    file_path = os.path.join(settings.SECURE_ROOT, filename)

    if result.status != 3 or not file_path or not os.path.exists(file_path):
        raise Http404("Report not found")

    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename={}".format(os.path.basename(file_path))
    return response


@require_http_methods(["GET"])
def report_view_csv(request, pk):
    # Generate the report
    report_name, report_headers, query = reports_backend.generate_full_report(pk)

    # Create a buffer to hold the CSV and assign a writer to it
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write the header
    writer.writerow(report_headers.values())
    for line in query:
        writer.writerow([line[header] for header in report_headers])

    # Seek to the start of the stream
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="text/csv")
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    response["Content-Disposition"] = f"attachment; filename=report_{timestamp}.csv"
    return response
