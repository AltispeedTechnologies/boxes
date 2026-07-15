"""Payment and invoice display template tags."""
from django import template


register = template.Library()


@register.simple_tag
def card_brand_display(brand):
    """Human label for a card brand code."""
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
    """Human label for invoice PaymentIntent state int."""
    invoice_states = {
        0: "Requires Confirmation",
        1: "Requires Action",
        2: "Processing",
        3: "Succeeded",
        4: "Failed"
    }
    return invoice_states.get(state, "Unknown")
