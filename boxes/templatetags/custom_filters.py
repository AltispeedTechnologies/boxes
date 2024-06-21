import pytz
from datetime import datetime
from django import template
from django.utils import timezone


register = template.Library()


@register.filter(name="get")
def get_item(dictionary, key):
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
    item = dictionary.get(key)
    if item is None:
        item = ""
    elif key == "price":
        item = "$" + str(item)
    elif isinstance(item, datetime):
        new_tz = pytz.timezone("America/Chicago")
        local_dt = item.astimezone(new_tz)
        item = local_dt.strftime("%b %d, %Y %I:%M:%S %p")

    return item


@register.filter(name="is_timestamp")
def is_timestamp(dictionary, key):
    return isinstance(dictionary.get(key), datetime)
