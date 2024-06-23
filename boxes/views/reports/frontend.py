import os
from boxes.models import GlobalSettings, Report, ReportResult
from boxes.tasks import generate_report_pdf
from boxes.backend import reports as reports_backend
from django.conf import settings
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def reports(request):
    reports = Report.objects.values("id", "name")

    return render(request, "reports/index.html", {"reports": reports})


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
                                                 "page_obj": page_obj})


@require_http_methods(["GET"])
def report_view_pdf(request, pk):
    result, _ = ReportResult.objects.get_or_create(report_id=pk)
    filename = result.pdf_path
    file_path = os.path.join(settings.SECURE_ROOT, filename)

    if result.status != 2 or not file_path or not os.path.exists(file_path):
        raise Http404("Report not found")

    response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename={}".format(os.path.basename(file_path))
    return response
