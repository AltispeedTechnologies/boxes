"""Customer-portal template helpers for cards and money formatting."""
from django import template


register = template.Library()
CARD_TYPE_LENGTHS = {
    "amex": 15,
    "diners": 14,
    "discover": 16,
    "eftpos_au": 16,
    "jcb": 16,
    "mastercard": 16,
    "unionpay": 16,
    "visa": 16
}


@register.simple_tag
def get_card_logo(brand):
    """Font Awesome class string for a payment brand."""
    icon_name = "fa-brands "

    match brand:
        case "amazon_pay":
            icon_name += "fa-cc-amazon-pay"
        case "amex":
            icon_name += "fa-cc-amex"
        case "bank":
            icon_name = "fa-solid fa-building-columns"
        case "cashapp":
            icon_name = "fa-solid fa-wallet"
        case "diners":
            icon_name += "fa-cc-diners-club"
        case "discover":
            icon_name += "fa-cc-discover"
        case "jcb":
            icon_name += "fa-cc-jcb"
        case "mastercard":
            icon_name += "fa-cc-mastercard"
        case "visa":
            icon_name += "fa-cc-visa"
        case _:
            icon_name += "fa-cc-stripe"

    return icon_name


@register.simple_tag
def get_card_number(card_type, last_four):
    """Masked card number display for brand + last four."""
    total_length = CARD_TYPE_LENGTHS.get(card_type, 16)
    num_asterisks = total_length - 4

    if card_type == "amex":
        return f"{'*' * 4} {'*' * 6} {'*' * 5} {last_four}"
    elif card_type == "diners":
        return f"{'*' * 4} {'*' * 6} {'*' * 4} {last_four}"
    else:
        return f"{'*' * 4} {'*' * 4} {'*' * 4} {'*' * (num_asterisks - 12)} {last_four}"


@register.filter
def format_negative(value):
    """Format number as currency; negatives as ``$(x.xx)``."""
    decimal_places = 2
    try:
        value = float(value)
        formatted_value = f'${value:,.{decimal_places}f}'
        if value < 0:
            return f'$({formatted_value[2:]})'
        return formatted_value
    except (ValueError, TypeError):
        return value
