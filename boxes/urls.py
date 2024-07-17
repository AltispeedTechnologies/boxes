from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, reverse
from django.urls import path, URLPattern, URLResolver
from boxes.views import *
from boxes.views.mgmt import *
from boxes.views.packages import *
from boxes.views.reports import *


def is_staff(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        elif not request.user.is_staff():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapped_view


def is_customer(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        elif not request.user.is_customer():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapped_view


def decorate_urlpatterns(urlpatterns, decorator):
    for i in range(len(urlpatterns)):
        if isinstance(urlpatterns[i], URLPattern):
            urlpatterns[i].callback = decorator(urlpatterns[i].callback)
        elif isinstance(urlpatterns[i], URLResolver):
            decorate_urlpatterns(urlpatterns[i].url_patterns, decorator)
    return urlpatterns


public_urlpatterns = [
    path("login/", sign_in, name="login"),
    path("webhooks/stripe", stripe_webhooks, name="stripe_webhooks"),
]


customer_urlpatterns = [
    path("", index, name="home"),
    path("logout/", sign_out, name="logout"),
    path("customer/payments", customer_make_payment, name="customer_make_payment"),
    path("customer/payments/portal", customer_payment_methods, name="customer_payment_methods"),
    path("customer/payments/portal/redir", customer_billing_portal, name="customer_billing_portal"),
    path("invoice/new", customer_new_invoice, name="customer_new_invoice"),
    path("invoice/<int:pk>", customer_view_invoice, name="customer_view_invoice"),
    path("invoice/<int:pk>/cancel", customer_cancel_invoice, name="customer_cancel_invoice"),
    path("invoice/<int:pk>/confirm", customer_confirm_invoice, name="customer_confirm_invoice"),
]


staff_urlpatterns = [
    # Management dropdown
    path("mgmt/accounts", account_mgmt, name="account_mgmt"),
    path("mgmt/charges", charge_settings, name="charge_settings"),
    path("mgmt/charges/update", save_charge_settings, name="save_charge_settings"),
    path("mgmt/email/configure", email_settings, name="email_settings"),
    path("mgmt/email/logs", email_logs, name="email_logs"),
    path("mgmt/email/update", save_email_settings, name="save_email_settings"),
    path("mgmt/email/templates", email_template, name="email_template"),
    path("mgmt/email/templates/add", add_email_template, name="add_email_template"),
    path("mgmt/email/templates/fetch", email_template_content, name="email_template_content"),
    path("mgmt/email/templates/update", update_email_template, name="update_email_template"),
    path("mgmt/general", general_settings, name="general_settings"),
    path("mgmt/general/update", save_general_settings, name="save_general_settings"),
    path("mgmt/packages/carriers", carrier_settings, name="carrier_settings"),
    path("mgmt/packages/carriers/update", update_carriers, name="update_carriers"),
    path("mgmt/packages/types", package_type_settings, name="package_type_settings"),
    path("mgmt/packages/types/update", update_package_types, name="update_package_types"),

    # Accounts
    path("accounts/<int:pk>/edit", account_edit, name="account_edit"),
    path("accounts/<int:pk>/emails", account_emails, name="account_emails"),
    path("accounts/<int:pk>/ledger", account_ledger, name="account_ledger"),
    path("accounts/<int:pk>/packages", account_packages, name="account_packages"),
    path("accounts/<int:pk>/update", update_account, name="update_account"),
    path("accounts/aliases/update", update_account_aliases, name="update_account_aliases"),
    path("accounts/search", account_search, name="account_search"),

    # Backend endpoints
    path("carriers/search", carrier_search, name="carrier_search"),
    path("emails/<int:pk>/contents", get_email_contents, name="get_email_contents"),
    path("picklists/query", picklist_query, name="picklist_query"),
    path("types/search", type_search, name="type_search"),
    path("modals/bulk", get_bulk_modals, name="get_bulk_modals"),
    path("modals/actions", get_actions_modals, name="get_actions_modals"),
    path("modals/picklistmgmt", get_picklist_mgmt_modals, name="get_picklist_mgmt_modals"),

    # Generic package information
    path("packages/", all_packages, name="packages"),
    path("packages/<int:pk>", package_detail, name="package_detail"),
    path("packages/<int:pk>/update", update_package, name="update_package"),
    path("packages/update", update_packages, name="update_packages"),

    # Search page
    path("packages/search", search_packages, name="search_packages"),

    # Check in page
    path("packages/checkin", check_in, name="check_in"),
    path("packages/checkin/create", create_package, name="create_package"),
    path("packages/checkin/submit", check_in_packages, name="check_in_packages"),

    # Check out page
    path("packages/checkout", check_out, name="check_out"),
    path("packages/checkout/submit", check_out_packages, name="check_out_packages"),
    path("packages/checkout/reverse", check_out_packages_reverse, name="check_out_packages_reverse"),
    path("packages/checkout/verify", verify_can_checkout, name="verify_can_checkout"),

    # Picklists page
    path("picklists/", picklist_list, name="picklists"),
    path("picklists/<int:pk>/checkout", picklist_check_out, name="picklist_check_out"),
    path("picklists/<int:pk>/packages", picklist_show, name="picklist_show"),
    path("picklists/<int:pk>/packages/table", picklist_show_table, name="picklist_show_table"),
    path("picklists/<int:pk>/remove", remove_picklist, name="remove_picklist"),
    path("picklists/create", create_picklist, name="create_picklist"),
    path("picklists/modify", modify_package_picklist, name="modify_package_picklist"),
    path("picklists/remove", remove_package_picklist, name="remove_package_picklist"),

    # Label printing
    path("packages/label", show_label, name="show_label"),
    path("packages/label/pdf", generate_label, name="generate_label"),

    # Basic queue data
    path("queues/<int:pk>/packages", queue_packages, name="queue_packages"),
    path("queues/<int:pk>/update", update_queue_name, name="update_queue_name"),

    # Users
    path("users/new", create_user, name="create_user"),
    path("users/update", update_user, name="update_user"),
    path("users/emails/update", update_user_emails, name="update_user_emails"),

    # Reports
    path("reports/data", report_data, name="report_data"),
    path("reports/data/view", report_data_view, name="report_data_view"),
    path("reports/list", report_list, name="report_list"),
    path("reports/name", report_name_search, name="report_name_search"),
    path("reports/new", report_details, name="report_new"),
    path("reports/new/submit", report_new_submit, name="report_new_submit"),
    path("reports/<int:pk>/csv", report_view_csv, name="report_generate_csv"),
    path("reports/<int:pk>/edit", report_details, name="report_details"),
    path("reports/<int:pk>/pdf", report_generate_pdf, name="report_generate_pdf"),
    path("reports/<int:pk>/pdf/view", report_view_pdf, name="report_view_pdf"),
    path("reports/<int:pk>/remove", report_remove, name="report_remove"),
    path("reports/<int:pk>/update", report_update, name="report_update"),
    path("reports/<int:pk>/view", report_view, name="report_view"),
    path("reports/stats/chart", report_stats_chart, name="report_stats_chart")
]

staff_urlpatterns = decorate_urlpatterns(staff_urlpatterns, is_staff)
customer_urlpatterns = decorate_urlpatterns(customer_urlpatterns, is_customer)

urlpatterns = [
    path("admin/", admin.site.urls),
] + public_urlpatterns + staff_urlpatterns + customer_urlpatterns
