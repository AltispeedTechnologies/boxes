"""Navigation and pagination template tags for reports and lists."""
from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, per_page=None):
    """Build pagination query string preserving q/filter/frequency/chart/per_page."""
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
    """Bootstrap button class for selected chart frequency."""
    frequency = context.get("frequency")
    set_class = "btn "
    set_class += "btn-primary" if frequency == freq else "btn-light"

    return set_class


@register.simple_tag(takes_context=True)
def data_tab_is_selected(context, chart):
    """Nav link class for active data tab."""
    current_chart = context.get("chart")
    set_class = "flex-sm-fill text-sm-center nav-link "
    set_class += "active" if chart == current_chart else "bg-light"

    return set_class


@register.simple_tag(takes_context=True)
def chart_tab_is_selected(context, freq):
    """Nav link class for active chart frequency tab."""
    frequency = context.get("frequency")
    set_class = "flex-sm-fill text-sm-center nav-link "
    set_class += "active" if frequency == freq else "bg-light"

    return set_class
