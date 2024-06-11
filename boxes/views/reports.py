import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import PackageLedger, SentEmail
from datetime import datetime, timedelta
from django.db.models import Count, Case, When, IntegerField
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def reports(request):
    return render(request, "reports/index.html")


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
