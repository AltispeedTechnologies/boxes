"""Smoke tests for split templatetag modules."""
from django.template import Context, Template
from django.test import SimpleTestCase


class TemplatetagSmokeTests(SimpleTestCase):
    def test_dict_get_filter(self):
        tpl = Template("{% load dict_filters %}{{ d|get:'a' }}")
        out = tpl.render(Context({"d": {"a": "ok"}}))
        self.assertEqual(out, "ok")

    def test_dict_get_item_or_unknown(self):
        tpl = Template("{% load dict_filters %}{{ d|get_item:'missing' }}")
        out = tpl.render(Context({"d": {}}))
        self.assertEqual(out, "Unknown")

    def test_payment_filters_card_brand(self):
        tpl = Template("{% load payment_filters %}{% card_brand_display 'visa' %}")
        out = tpl.render(Context({}))
        self.assertEqual(out, "Visa")

    def test_payment_filters_invoice_state(self):
        tpl = Template("{% load payment_filters %}{% invoice_state_display 3 %}")
        out = tpl.render(Context({}))
        self.assertEqual(out, "Succeeded")

    def test_nav_filters_load(self):
        tpl = Template("{% load nav_filters %}x")
        self.assertEqual(tpl.render(Context({})), "x")
