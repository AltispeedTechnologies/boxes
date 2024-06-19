import json
import re
from boxes.management.exception_catcher import exception_catcher
from boxes.models import Package, PackageLedger, Report, SentEmail
from datetime import datetime, timedelta
from django.db.models import Count, Case, CharField, F, IntegerField, Max, Q, Value, When
from django.db.models.functions import Concat, TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def reports(request):
    reports = Report.objects.values("id", "name")

    return render(request, "reports/index.html", {"reports": reports})


@require_http_methods(["GET"])
@exception_catcher()
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
    report = Report.objects.filter(pk=pk).first()
    config = report.config

    # Define the base query - this will get more specific
    query = Package.objects.all()
    combined_filters = Q()

    # Filter by a specific state
    match config["state"]:
        case "in":
            combined_filters &= Q(packageledger__state=1)
        case "out":
            combined_filters &= Q(packageledger__state=2)

    # Filter by a specific date range if applicable
    match config["filter"]["type"]:
        case "date_range":
            end = datetime.strptime(config["filter"]["end"], "%m/%d/%Y")
            end = timezone.make_aware(end)
            start = datetime.strptime(config["filter"]["start"], "%m/%d/%Y")
            start = timezone.make_aware(start)
            combined_filters &= Q(packageledger__timestamp__gte=start, packageledger__timestamp__lte=end)
        case "relative_date_range":
            now = timezone.now()
            end = now - timedelta(days=config["filter"]["end"])
            start = now - timedelta(days=config["filter"]["start"])
            combined_filters &= Q(packageledger__timestamp__gte=end, packageledger__timestamp__lte=start)
        case "time_period":
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

            match config["filter"]["frequency"]:
                case "day":
                    combined_filters &= Q(packageledger__timestamp__gte=today)
                case "week":
                    days_since_sun = (today.weekday() + 1) % 7
                    this_week = today - timedelta(days=days_since_sun)
                    combined_filters &= Q(packageledger__timestamp__gte=this_week)
                case "month":
                    this_month = today.replace(day=1)
                    combined_filters &= Q(packageledger__timestamp__gte=this_month)
                case "year":
                    this_year = today.replace(month=1, day=1)
                    combined_filters &= Q(packageledger__timestamp__gte=this_year)

    # Apply the combined filters
    query = query.filter(combined_filters)

    # Only get the values selected
    field_annotations = {
        "account_name": F("account__name"),
        "carrier_name": F("carrier__name"),
        "check_in_time": Max(Case(
            When(packageledger__state=1, then="packageledger__timestamp")
        )),
        "check_out_time": Max(Case(
            When(packageledger__state=2, then="packageledger__timestamp")
        )),
        "checked_in_by": Concat(
            Case(
                When(packageledger__state=1, then=F("packageledger__user__first_name")),
                default=Value(""),
                output_field=CharField()
            ),
            Value(" "),
            Case(
                When(packageledger__state=1, then=F("packageledger__user__last_name")),
                default=Value(""),
                output_field=CharField()
            ),
            output_field=CharField()
        ),
        "checked_out_by": Concat(
            Case(
                When(packageledger__state=2, then=F("packageledger__user__first_name")),
                default=Value(""),
                output_field=CharField()
            ),
            Value(" "),
            Case(
                When(packageledger__state=2, then=F("packageledger__user__last_name")),
                default=Value(""),
                output_field=CharField()
            ),
            output_field=CharField()
        ),
        "package_type_desc": F("package_type__description"),
        "status": F("current_state")
    }
    # Annotate queryset
    fields_to_include = {f: field_annotations[f] for f in config["fields"] if f in field_annotations}
    query = query.annotate(**fields_to_include)

    # Include all necessary values, including the annotations
    allowed_fields = ["account_name", "carrier_name", "check_in_time", "check_out_time", "checked_in_by",
                      "checked_out_by", "comments", "inside", "package_type_desc", "price", "status", "tracking_code"]
    fields_to_include = [f for f in config["fields"] if f in allowed_fields]
    query = query.values(*fields_to_include)

    # Sort by a specific key
    query = query.order_by(config["sort_by"])

    # Set the column headers appropriately
    column_headers = {
        "account_name": "Account",
        "carrier_name": "Carrier",
        "check_in_time": "Check In Time",
        "check_out_time": "Check Out Time",
        "checked_in_by": "Checked In By",
        "checked_out_by": "Checked Out By",
        "comments": "Comments",
        "inside": "Inside",
        "package_type_desc": "Type",
        "price": "Price",
        "status": "Status",
        "tracking_code": "Tracking Code"
    }
    report_headers = {f: column_headers[f] for f in fields_to_include}

    return render(request, "reports/view.html", {"report_name": report.name,
                                                 "report_headers": report_headers,
                                                 "report": query})


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


def clean_config(config):
    # Ensure the top-level keys are present
    for main_key in ["fields", "sort_by", "filter", "state"]:
        if main_key not in config:
            return False

    # Enforce data types for the top-level keys
    if not type(config["fields"]) is list:
        return False
    elif not type(config["sort_by"]) is str:
        return False
    elif not type(config["filter"]) is dict:
        return False
    elif not type(config["state"]) is str:
        return False

    # Only allow specific values in fields
    allowed_fields = ["account_name", "carrier_name", "check_in_time", "check_out_time", "checked_in_by",
                      "checked_out_by", "comments", "inside", "package_type_desc", "price", "status", "tracking_code"]
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
            elif config["filter"]["end"] <= config["filter"]["start"]:
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

    # The state should match one of three options
    allowed_states = ["all", "in", "out"]
    if config["state"] not in allowed_states:
        return False

    return True


@require_http_methods(["POST"])
@exception_catcher()
def report_new_submit(request):
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
    elif not clean_config(config):
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
