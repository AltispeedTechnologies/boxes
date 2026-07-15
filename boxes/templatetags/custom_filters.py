"""Compatibility re-export of dict/nav/payment filters.

Prefer loading the focused modules in templates::

    {% load dict_filters %}
    {% load nav_filters %}
    {% load payment_filters %}

Filter and tag *names* remain stable across the split.
"""
from django import template

from boxes.templatetags import dict_filters, nav_filters, payment_filters

register = template.Library()
register.filters.update(dict_filters.register.filters)
register.filters.update(nav_filters.register.filters)
register.filters.update(payment_filters.register.filters)
register.tags.update(dict_filters.register.tags)
register.tags.update(nav_filters.register.tags)
register.tags.update(payment_filters.register.tags)
