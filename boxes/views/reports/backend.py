import json
from boxes.backend import reports as reports_backend
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Report, ReportResult
from boxes.tasks.pdf import generate_report_pdf
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
@exception_catcher()
def report_name_search(request):
    data = json.loads(request.body)
    name = data.get("name", None)
    if name:
        is_unique = Report.objects.filter(name=name).count() == 0
    else:
        is_unique = False
    return JsonResponse({"success": True, "unique": is_unique})


@require_http_methods(["POST"])
@exception_catcher()
def report_new_submit(request):
    data = json.loads(request.body)
    name = data.get("name", None)
    config = data.get("config", None)

    # The UI prevents this all from happening, just safeguards
    if not name or not config:
        raise ValueError
    elif not reports_backend.clean_config(config):
        raise ValueError
    elif len(name) > 64:
        raise ValueError
    elif Report.objects.filter(name=name).count() > 0:
        return JsonResponse({"success": False,
                             "form_errors": {"reportname": ["Name already exists"]}})

    Report.objects.create(name=name, config=config)


@require_http_methods(["POST"])
@exception_catcher()
def report_update(request, pk):
    data = json.loads(request.body)
    name = data.get("name", None)
    config = data.get("config", None)

    # The UI prevents this all from happening, just safeguards
    if not name or not config:
        raise ValueError
    elif not reports_backend.clean_config(config):
        raise ValueError
    elif len(name) > 64:
        raise ValueError

    Report.objects.filter(pk=pk).update(name=name, config=config)


@require_http_methods(["POST"])
@exception_catcher()
def report_remove(request, pk):
    Report.objects.filter(pk=pk).delete()


# Chart on main reports page
@require_http_methods(["POST"])
@exception_catcher()
def report_stats_chart(request):
    data = json.loads(request.body)
    x_data, y_data = reports_backend.report_chart_generate(data)

    return JsonResponse({"success": True, "x_data": x_data, "y_data": y_data})


def report_generate_pdf(request, pk):
    if request.method == "POST":
        # Fetch the result for this report or create one
        result, _ = ReportResult.objects.get_or_create(report_id=pk)
        # Mark as being in the queue
        result.status = 1
        result.save()

        generate_report_pdf.delay(pk)

        return JsonResponse({"success": True})
    elif request.method == "GET":
        result, _ = ReportResult.objects.get_or_create(report_id=pk)

        return JsonResponse({"success": True, "current_status": result.status, "current_progress": result.progress})
