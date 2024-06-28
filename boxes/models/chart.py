from django.db import models

CHART_FREQUENCIES = [
    ("T", "Today"),
    ("W", "Week"),
    ("M", "Month"),
    ("Q", "Quarter"),
    ("Y", "Year")
]


class Chart(models.Model):
    frequency = models.CharField(choices=CHART_FREQUENCIES)
    last_updated = models.DateTimeField()
    chart_data = models.JSONField(null=True)
    total_data = models.JSONField()
