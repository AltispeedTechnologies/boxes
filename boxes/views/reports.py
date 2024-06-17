import json
import re
from boxes.management.exception_catcher import exception_catcher
from boxes.models import PackageLedger, Report, SentEmail
from datetime import datetime, timedelta
from django.db.models import Count, Case, When, IntegerField
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def reports(request):
    reports = Report.objects.values("id", "name")

    return render(request, "reports/index.html", {"reports": reports})


def clean_config(config):
    # Ensure the top-level keys are present
    for main_key in ["fields", "sort_by", "filter"]:
        if main_key not in config:
            return False

    # Enforce data types for the top-level keys
    if not type(config["fields"]) is list:
        return False
    elif not type(config["sort_by"]) is str:
        return False

    # Only allow specific values in fields
    allowed_fields = ["account", "carrier", "check_in_time", "check_out_time", "checked_in_by", "checked_out_by",
                      "comment", "inside", "package_type", "price", "status", "tracking_code"]
    for field in config["fields"]:
        if field not in allowed_fields:
            return False

    # We should only sort by a known field
    if config["sort_by"] not in allowed_fields:
        return False

    # Ensure a strict format is followed for the filter
    allowed_filter_types = ["all", "date_range", "relative_date_range", "time_period"]
    if "type" not in config["filter"].keys():
        return False
    elif config["filter"]["type"] not in allowed_filter_types:
        return False

    match config["filter"]["type"]:
        case "all":
            # There should only be the type key, any other keys are not allowed
            if len(config["filter"].keys()) != 1:
                return False
        case "date_range":
            # There should only be a type, start, and end - enforce this
            if len(config["filter"].keys()) != 3:
                return False
            elif "start" not in config["filter"].keys() or "end" not in config["filter"].keys():
                return False

            # MM/DD/YYYY
            pattern = r"^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/(20[0-9][0-9])$"
            # Ensure both dates passed match the above format
            if not re.match(pattern, config["filter"]["start"]) or not re.match(pattern, config["filter"]["end"]):
                return False

            # Ensure the start time is never greater than the end time
            start_date = datetime.strptime(config["filter"]["start"], "%m/%d/%Y").date()
            end_date = datetime.strptime(config["filter"]["end"], "%m/%d/%Y").date()
            if start_date > end_date:
                return False
        case "relative_date_range":
            # There should only be a type, start, and end - enforce this
            if len(config["filter"].keys()) != 3:
                return False
            elif "start" not in config["filter"].keys() or "end" not in config["filter"].keys():
                return False

            # Both items must be ints
            if not isinstance(config["filter"]["start"], int) or not isinstance(config["filter"]["end"], int):
                return False
            # End must be greater than the start
            elif config["filter"]["start"] <= config["filter"]["end"]:
                return False
        case "time_period":
            # There should only be a type and frequency - enforce this
            if len(config["filter"].keys()) != 2:
                return False
            elif "frequency" not in config["filter"].keys():
                return False

            # Frequency must be one of: day, week, month, year
            if config["filter"]["frequency"] not in ["day", "week", "month", "year"]:
                return False

    return True


@require_http_methods(["POST"])
@exception_catcher()
def report_new(request):
    data = json.loads(request.body)
    name = data.get("name", None)
    config = data.get("config", None)

    # The UI prevents this all from happening, just safeguards
    if not name or not config:
        raise ValueError
    elif not clean_config(config):
        raise ValueError
    elif len(name) > 64:
        raise ValueError
    elif Report.objects.filter(name=name).count() > 0:
        return JsonResponse({"success": False,
                             "form_errors": {"reportname": ["Name already exists"]}})

    new_report = Report.objects.create(name=name, config=config)
    return JsonResponse({"success": True, "id": new_report.id})


@require_http_methods(["POST"])
@exception_catcher()
def report_remove(request, pk):
    Report.objects.filter(pk=pk).delete()


# Chart on main reports page
@require_http_methods(["POST"])
@exception_catcher()
def report_stats_chart(request):
    data = json.loads(request.body)
    timeframe_filter = data.get("filter")
    if timeframe_filter == "week":
        days = 7
    elif timeframe_filter == "month":
        days = 30

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    starting_point = today - timedelta(days=days)

    # Prepare date list for x-axis
    x_data = [(starting_point + timedelta(days=i)).strftime("%m/%d/%Y") for i in range(days + 1)]

    # Query PackageLedger
    package_counts = PackageLedger.objects.filter(
        timestamp__gte=starting_point,
        timestamp__lt=today + timedelta(days=1)
    ).annotate(
        date=TruncDay("timestamp")
    ).values("date").annotate(
        packages_in=Count(Case(When(state=1, then=1), output_field=IntegerField())),
        packages_out=Count(Case(When(state=2, then=1), output_field=IntegerField()))
    ).order_by("date")

    # Query SentEmail
    email_counts = SentEmail.objects.filter(
        timestamp__gte=starting_point,
        timestamp__lt=today + timedelta(days=1)
    ).annotate(
        date=TruncDay("timestamp")
    ).values("date").annotate(
        emails_sent=Count('id')
    ).order_by("date")

    # Prepare data structures for response
    y_data = {
        "Packages In": [0] * (days + 1),
        "Packages Out": [0] * (days + 1),
        "Emails Sent": [0] * (days + 1)
    }

    # Map counts to the correct date indices
    start_date_index = {
        date.strftime("%m/%d/%Y"): i
        for i, date in enumerate(
            (starting_point + timedelta(days=i)) for i in range(days + 1)
        )
    }

    # Combine data
    for count in package_counts:
        index = start_date_index[count["date"].strftime("%m/%d/%Y")]
        y_data["Packages In"][index] = count["packages_in"]
        y_data["Packages Out"][index] = count["packages_out"]

    for count in email_counts:
        index = start_date_index[count["date"].strftime("%m/%d/%Y")]
        y_data["Emails Sent"][index] = count["emails_sent"]

    return JsonResponse({"success": True, "x_data": x_data, "y_data": y_data})
