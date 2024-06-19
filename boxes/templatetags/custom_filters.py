from datetime import datetime
from django import template


register = template.Library()


@register.filter(name="get")
def get_item(dictionary, key):
    item = dictionary.get(key)
    if item is None:
        item = ""

    if isinstance(item, datetime):
        item = item.isoformat()

    return item


@register.filter(name="is_timestamp")
def is_timestamp(dictionary, key):
    return isinstance(dictionary.get(key), datetime)
