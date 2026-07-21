"""Explicit exports for management settings views."""
from boxes.views.mgmt.accounts import account_mgmt
from boxes.views.mgmt.carriers import carrier_settings, update_carriers
from boxes.views.mgmt.charges import charge_settings, save_charge_settings
from boxes.views.mgmt.email import email_logs, email_settings, save_email_settings
from boxes.views.mgmt.email_templates import (
    add_email_template,
    email_template,
    email_template_content,
    update_email_template,
)
from boxes.views.mgmt.general import general_settings, save_general_settings
from boxes.views.mgmt.pickup import (
    pickup_mgmt,
    pickup_open_days,
    update_pickup_days,
    update_pickup_rules,
)
from boxes.views.mgmt.setup_status import mgmt_setup_status_api
from boxes.views.mgmt.types import package_type_settings, update_package_types

__all__ = [
    "account_mgmt",
    "add_email_template",
    "carrier_settings",
    "charge_settings",
    "email_logs",
    "email_settings",
    "email_template",
    "email_template_content",
    "general_settings",
    "mgmt_setup_status_api",
    "package_type_settings",
    "pickup_mgmt",
    "pickup_open_days",
    "save_charge_settings",
    "save_email_settings",
    "save_general_settings",
    "update_carriers",
    "update_email_template",
    "update_package_types",
    "update_pickup_days",
    "update_pickup_rules",
]
