import pytz
from datetime import datetime
from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe


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


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key, "Unknown")


@register.simple_tag(takes_context=True)
def query_string(context, per_page=None):
    per_page = per_page or context["request"].GET.get("per_page") or 10
    query_string = f"&per_page={per_page}"

    query = context.get("query")
    filter_val = context.get("filter")
    frequency = context.get("frequency")
    chart = context.get("chart")

    if query:
        query_string += f"&q={query}"
    if filter_val:
        query_string += f"&filter={filter_val}"
    if frequency:
        query_string += f"&frequency={frequency}"
    if chart:
        query_string += f"&chart={chart}"

    return mark_safe(query_string)


@register.simple_tag(takes_context=True)
def chart_is_selected(context, freq):
    frequency = context.get("frequency")
    set_class = "btn "
    set_class += "btn-primary" if frequency == freq else "btn-light"

    return set_class


@register.simple_tag(takes_context=True)
def data_tab_is_selected(context, chart):
    current_chart = context.get("chart")
    set_class = "flex-sm-fill text-sm-center nav-link "
    set_class += "active" if chart == current_chart else "bg-light"

    return set_class


@register.simple_tag(takes_context=True)
def chart_tab_is_selected(context, freq):
    frequency = context.get("frequency")
    set_class = "flex-sm-fill text-sm-center nav-link "
    set_class += "active" if frequency == freq else "bg-light"

    return set_class


@register.simple_tag
def card_brand_display(brand):
    if brand in ["cashapp", "amazon_pay", "bank"]:
        return ""

    card_brands = {
        "amex": "American Express",
        "diners": "Diners Club",
        "discover": "Discover",
        "eftpos_au": "Eftpos AU",
        "jcb": "JCB",
        "mastercard": "MasterCard",
        "unionpay": "UnionPay",
        "visa": "Visa",
        "unknown": "Unknown"
    }
    return card_brands.get(brand, "Unknown")


@register.simple_tag
def invoice_state_display(state):
    invoice_states = {
        0: "Requires Confirmation",
        1: "Requires Action",
        2: "Processing",
        3: "Succeeded",
        4: "Failed"
    }
    return invoice_states.get(state, "Unknown")
