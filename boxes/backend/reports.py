import json
import re
from boxes.models import Package, PackageLedger, Report, SentEmail
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.db.models import (Count, Case, CharField, DateTimeField, F, IntegerField, Max, OuterRef, Q, Subquery,
                              Value, When)
from django.db.models.functions import Concat, TruncDay
from django.utils import timezone


def _datetime_from_period(period):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_period = None

    match period:
        case "day" | "T":
            new_period = today
        case "week" | "W":
            days_since_sun = (today.weekday() + 1) % 7
            new_period = today - timedelta(days=days_since_sun)
        case "month" | "M":
            new_period = today.replace(day=1)
        case "Q":
            current_quarter = (today.month - 1) // 3 + 1
            start_month = 3 * (current_quarter - 1) + 1
            new_period = today.replace(month=start_month, day=1)
        case "year" | "Y":
            new_period = today.replace(month=1, day=1)

    days = (today - new_period).days

    return today, new_period, days


def generate_full_report(pk):
    report = Report.objects.filter(pk=pk).first()
    config = report.config

    # Define the base query - this will get more specific
    query = Package.objects.all()
    combined_filters = Q()

    # Subqueries for filters
    latest_check_in = PackageLedger.objects.filter(
        package=OuterRef("pk"),
        state=1
    ).order_by("-timestamp").values("timestamp")[:1]
    latest_check_out = PackageLedger.objects.filter(
        package=OuterRef("pk"),
        state=2
    ).order_by("-timestamp").values("timestamp")[:1]
    latest_checked_in_by = PackageLedger.objects.filter(
        package=OuterRef("pk"),
        state=1
    ).order_by("-timestamp").annotate(
        full_name=Concat("user__first_name", Value(" "), "user__last_name", output_field=CharField())
    ).values("full_name")[:1]
    latest_checked_out_by = PackageLedger.objects.filter(
        package=OuterRef("pk"),
        state=2
    ).order_by("-timestamp").annotate(
        full_name=Concat("user__first_name", Value(" "), "user__last_name", output_field=CharField())
    ).values("full_name")[:1]

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
            _, this_period, _ = _datetime_from_period(config["filter"]["frequency"])
            combined_filters &= Q(packageledger__timestamp__gte=this_period)

    # Apply the combined filters
    query = query.filter(combined_filters)

    # Only get the values selected
    field_annotations = {
        "account_name": F("account__name"),
        "carrier_name": F("carrier__name"),
        "check_in_time": Subquery(latest_check_in, output_field=DateTimeField()),
        "check_out_time": Subquery(latest_check_out, output_field=DateTimeField()),
        "checked_in_by": Subquery(latest_checked_in_by, output_field=CharField()),
        "checked_out_by": Subquery(latest_checked_out_by, output_field=CharField()),
        "package_type_desc": F("package_type__description"),
        "status": Max(Case(
            When(current_state=0, then=Value("Received")),
            When(current_state=1, then=Value("Checked in")),
            When(current_state=2, then=Value("Checked out")),
            When(current_state=3, then=Value("Mis-placed")),
            default=Value("Unknown"),
            output_field=CharField(),
        ))
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

    return report.name, report_headers, query


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


def report_chart_generate(timeframe_filter):
    today, starting_point, days = _datetime_from_period(timeframe_filter)

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
        emails_sent=Count("id")
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

    # Get totals for each column
    total_data = {
        "packages_in": 0,
        "packages_out": 0,
        "emails_sent": 0,
    }

    # Combine data
    for count in package_counts:
        index = start_date_index[count["date"].strftime("%m/%d/%Y")]
        y_data["Packages In"][index] = count["packages_in"]
        y_data["Packages Out"][index] = count["packages_out"]
        total_data["packages_in"] += count["packages_in"]
        total_data["packages_out"] += count["packages_out"]

    for count in email_counts:
        index = start_date_index[count["date"].strftime("%m/%d/%Y")]
        y_data["Emails Sent"][index] = count["emails_sent"]
        total_data["emails_sent"] += count["emails_sent"]

    chart_data = {"x_data": x_data, "y_data": y_data}

    return chart_data, total_data
