"""Dictionary lookup template filters for tables and PDFs."""
from datetime import datetime

from django import template
from django.utils import timezone


register = template.Library()


@register.filter(name="get")
def get_item(dictionary, key):
    """Dictionary lookup filter; formats price and datetimes for display (or Unknown default)."""
    item = dictionary.get(key)
    if item is None:
        item = ""
    elif key == "price":
        item = "$" + str(item)
    elif isinstance(item, datetime):
        item = item.isoformat()

    return item


@register.filter(name="get_pdf")
def get_item_pdf(dictionary, key):
    """Dictionary lookup formatted for PDF (localized timestamps)."""
    item = dictionary.get(key)
    if item is None:
        item = ""
    elif key == "price":
        item = "$" + str(item)
    elif isinstance(item, datetime):
        local_dt = timezone.localtime(item)
        item = local_dt.strftime("%b %d, %Y %I:%M:%S %p")

    return item


@register.filter(name="is_timestamp")
def is_timestamp(dictionary, key):
    """Return True if dictionary[key] is a datetime."""
    return isinstance(dictionary.get(key), datetime)


@register.filter(name="get_item")
def get_item_or_unknown(dictionary, key):
    """Dictionary lookup filter; formats price and datetimes for display (or Unknown default)."""
    return dictionary.get(key, "Unknown")
