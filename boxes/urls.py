"""URL routing with public, authenticated, staff, delivery, and customer tiers."""
from functools import wraps

from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, reverse
from django.urls import path, URLPattern, URLResolver
from boxes.views import (
    account_edit,
    account_emails,
    account_fee_waiver,
    account_ledger,
    account_members_create_web,
    account_members_disassociate,
    account_members_link,
    account_members_set_role,
    account_packages,
    account_search,
    carrier_search,
    create_picklist,
    create_user,
    customer_billing_portal,
    customer_cancel_invoice,
    customer_confirm_invoice,
    customer_invoices,
    customer_ledger,
    customer_make_payment,
    customer_new_invoice,
    customer_open_pickup_days,
    customer_parcels,
    customer_payment_methods,
    customer_reserve_pickup,
    customer_select_account,
    customer_view_invoice,
    customer_view_pdf,
    generate_label,
    get_actions_modals,
    get_bulk_modals,
    get_email_contents,
    get_picklist_mgmt_modals,
    index,
    mailjet_webhooks,
    modify_package_picklist,
    picklist_check_out,
    picklist_list,
    picklist_query,
    picklist_show,
    picklist_show_table,
    profile_user,
    remove_package_picklist,
    remove_picklist,
    send_user_invite,
    session_set_active_account,
    show_label,
    sign_in,
    sign_out,
    signup,
    stripe_webhooks,
    update_account,
    update_account_aliases,
    update_profile,
    update_profile_emails,
    update_user,
    update_user_emails,
    update_user_status,
    user_detail,
    user_link_account,
    user_mgmt,
    user_search,
    user_unlink_account,
    user_set_account_role,
)
from boxes.views.mgmt import (
    mgmt_setup_status_api,
    account_mgmt,
    add_email_template,
    carrier_settings,
    charge_settings,
    email_logs,
    email_settings,
    email_template,
    email_template_content,
    env_api_keys,
    general_settings,
    package_type_settings,
    pickup_mgmt,
    pickup_open_days,
    save_charge_settings,
    save_email_settings,
    save_general_settings,
    update_carriers,
    update_email_template,
    update_package_types,
    update_pickup_days,
    update_pickup_rules,
)
from boxes.views.packages import (
    all_packages,
    check_in,
    check_in_packages,
    check_out,
    check_out_packages,
    check_out_packages_reverse,
    create_package,
    package_detail,
    queue_packages,
    search_packages,
    type_search,
    update_package,
    update_packages,
    update_queue_name,
    verify_can_checkout,
)
from boxes.views.reports import (
    report_data,
    report_data_view,
    report_details,
    report_generate_pdf,
    report_list,
    report_name_search,
    report_new_submit,
    report_remove,
    report_stats_chart,
    report_update,
    report_view,
    report_view_csv,
    report_view_pdf,
    stripe_totals,
)


def is_staff(view_func):
    """Decorator: require login and Staff group (``has_staff_role``), else 403."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        """Staff-gated view wrapper."""
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        elif not request.user.has_staff_role():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    wrapped_view.access_tier = "staff"
    return wrapped_view


def is_delivery(view_func):
    """Decorator: require login and Delivery or Staff group, else 403.

    Staff retains warehouse-floor access for routes moved into
    ``delivery_urlpatterns``. Delivery-only users cannot reach staff-only paths.
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        """Delivery-or-staff gated view wrapper."""
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        user = request.user
        if not (user.has_delivery_role() or user.has_staff_role()):
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    wrapped_view.access_tier = "delivery"
    return wrapped_view


def is_customer(view_func):
    """Decorator: require login and Customer group, else 403."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        """Customer-gated view wrapper."""
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        elif not request.user.is_customer():
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    wrapped_view.access_tier = "customer"
    return wrapped_view


def _tag_access_tier(urlpatterns, tier):
    """Attach access_tier metadata to each pattern callback for introspection."""
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            cb = pattern.callback
            if not getattr(cb, "access_tier", None):
                try:
                    cb.access_tier = tier
                except (AttributeError, TypeError):
                    pass
        elif isinstance(pattern, URLResolver):
            _tag_access_tier(pattern.url_patterns, tier)
    return urlpatterns


def decorate_urlpatterns(urlpatterns, decorator):
    """Apply a decorator to every URLPattern callback in a list (recursive)."""
    for i in range(len(urlpatterns)):
        if isinstance(urlpatterns[i], URLPattern):
            urlpatterns[i].callback = decorator(urlpatterns[i].callback)
        elif isinstance(urlpatterns[i], URLResolver):
            decorate_urlpatterns(urlpatterns[i].url_patterns, decorator)
    return urlpatterns


public_urlpatterns = [
    path("login/", sign_in, name="login"),
    path("signup/<str:token>/", signup, name="signup"),
    path("webhooks/stripe", stripe_webhooks, name="stripe_webhooks"),
    path("webhooks/mailjet", mailjet_webhooks, name="mailjet_webhooks"),
]


customer_urlpatterns = [
    path("session/account", session_set_active_account, name="session_set_active_account"),
    path("customer/select-account", customer_select_account, name="customer_select_account"),
    path("customer/parcels", customer_parcels, name="customer_parcels"),
    path("customer/parcels/reserve", customer_reserve_pickup, name="customer_reserve_pickup"),
    path("customer/pickup/open", customer_open_pickup_days, name="customer_open_pickup_days"),
    path("customer/payments", customer_make_payment, name="customer_make_payment"),
    path("customer/payments/portal", customer_payment_methods, name="customer_payment_methods"),
    path("customer/payments/portal/redir", customer_billing_portal, name="customer_billing_portal"),
    path("customer/invoices", customer_invoices, name="customer_invoices"),
    path("customer/ledger", customer_ledger, name="customer_ledger"),
    path("invoice/new", customer_new_invoice, name="customer_new_invoice"),
    path("invoice/<int:pk>", customer_view_invoice, name="customer_view_invoice"),
    path("invoice/<int:pk>/cancel", customer_cancel_invoice, name="customer_cancel_invoice"),
    path("invoice/<int:pk>/confirm", customer_confirm_invoice, name="customer_confirm_invoice"),
    path("invoice/<int:pk>/pdf", customer_view_pdf, name="customer_view_pdf"),
]


# Warehouse-floor routes: Delivery group, and Staff (via is_delivery).
# Not account edit, not payments, not mgmt settings.
delivery_urlpatterns = [
    # Check in
    path("packages/checkin", check_in, name="check_in"),
    path("packages/checkin/create", create_package, name="create_package"),
    path("packages/checkin/submit", check_in_packages, name="check_in_packages"),
    path("queues/<int:pk>/packages", queue_packages, name="queue_packages"),

    # Select2 helpers for check-in / search
    path("accounts/search", account_search, name="account_search"),
    path("carriers/search", carrier_search, name="carrier_search"),
    path("types/search", type_search, name="type_search"),

    # Package search (read-only-ish) and detail
    path("packages/", all_packages, name="packages"),
    path("packages/search", search_packages, name="search_packages"),
    path("packages/<int:pk>", package_detail, name="package_detail"),
    path("accounts/<int:pk>/packages", account_packages, name="account_packages"),

    # Labels after check-in
    path("packages/label", show_label, name="show_label"),
    path("packages/label/pdf", generate_label, name="generate_label"),

    # Field fixes during check-in (not mgmt/account edit)
    path("packages/<int:pk>/update", update_package, name="update_package"),
    path("packages/update", update_packages, name="update_packages"),

    # Picklists: list, view, add package
    path("picklists/", picklist_list, name="picklists"),
    path("picklists/query", picklist_query, name="picklist_query"),
    path("picklists/modify", modify_package_picklist, name="modify_package_picklist"),
    path("picklists/<int:pk>/packages", picklist_show, name="picklist_show"),
    path("picklists/<int:pk>/packages/table", picklist_show_table, name="picklist_show_table"),
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
    path("mgmt/env-keys", env_api_keys, name="env_api_keys"),
    path("mgmt/general/update", save_general_settings, name="save_general_settings"),
    path("mgmt/packages/carriers", carrier_settings, name="carrier_settings"),
    path("mgmt/packages/carriers/update", update_carriers, name="update_carriers"),
    path("mgmt/packages/types", package_type_settings, name="package_type_settings"),
    path("mgmt/packages/types/update", update_package_types, name="update_package_types"),

    # Accounts
    path("accounts/<int:pk>/edit", account_edit, name="account_edit"),
    path("accounts/<int:pk>/emails", account_emails, name="account_emails"),
    path("accounts/<int:pk>/ledger", account_ledger, name="account_ledger"),
    path("accounts/<int:pk>/update", update_account, name="update_account"),
    path("accounts/<int:pk>/members/link", account_members_link, name="account_members_link"),
    path("accounts/<int:pk>/members/create", account_members_create_web, name="account_members_create_web"),
    path("accounts/<int:pk>/members/disassociate", account_members_disassociate, name="account_members_disassociate"),
    path("accounts/<int:pk>/members/role", account_members_set_role, name="account_members_set_role"),
    path("accounts/<int:pk>/waiver", account_fee_waiver, name="account_fee_waiver"),
    path("accounts/aliases/update", update_account_aliases, name="update_account_aliases"),

    # Pickup day management
    path("mgmt/pickup", pickup_mgmt, name="pickup_mgmt"),
    path("mgmt/pickup/open", pickup_open_days, name="pickup_open_days"),
    path("mgmt/pickup/rules/update", update_pickup_rules, name="update_pickup_rules"),
    path("mgmt/pickup/days/update", update_pickup_days, name="update_pickup_days"),

    # Backend endpoints
    path("emails/<int:pk>/contents", get_email_contents, name="get_email_contents"),
    path("modals/bulk", get_bulk_modals, name="get_bulk_modals"),
    path("modals/actions", get_actions_modals, name="get_actions_modals"),
    path("modals/picklistmgmt", get_picklist_mgmt_modals, name="get_picklist_mgmt_modals"),

    # Check out page
    path("packages/checkout", check_out, name="check_out"),
    path("packages/checkout/submit", check_out_packages, name="check_out_packages"),
    path("packages/checkout/reverse", check_out_packages_reverse, name="check_out_packages_reverse"),
    path("packages/checkout/verify", verify_can_checkout, name="verify_can_checkout"),

    # Picklist management beyond add-package
    path("picklists/<int:pk>/checkout", picklist_check_out, name="picklist_check_out"),
    path("picklists/<int:pk>/remove", remove_picklist, name="remove_picklist"),
    path("picklists/create", create_picklist, name="create_picklist"),
    path("picklists/remove", remove_package_picklist, name="remove_package_picklist"),

    # Queue rename
    path("queues/<int:pk>/update", update_queue_name, name="update_queue_name"),

    # Users (login identities; managed separately from billing accounts)
    path("mgmt/users", user_mgmt, name="user_mgmt"),
    path("mgmt/setup-status", mgmt_setup_status_api, name="mgmt_setup_status_api"),
    path("users/new", create_user, name="create_user"),
    path("users/search", user_search, name="user_search"),
    path("users/update", update_user, name="update_user"),
    path("users/emails/update", update_user_emails, name="update_user_emails"),
    path("users/invite", send_user_invite, name="send_user_invite"),
    path("users/<int:pk>/edit", user_detail, name="user_detail"),
    path("users/<int:pk>/status", update_user_status, name="update_user_status"),
    path("users/<int:pk>/invite", send_user_invite, name="send_user_invite_for"),
    path("users/<int:pk>/accounts/link", user_link_account, name="user_link_account"),
    path("users/<int:pk>/accounts/unlink", user_unlink_account, name="user_unlink_account"),
    path("users/<int:pk>/accounts/role", user_set_account_role, name="user_set_account_role"),

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
    path("reports/stats/chart", report_stats_chart, name="report_stats_chart"),
    path("reports/stripe-totals", stripe_totals, name="stripe_totals"),
]

# Shared routes for any authenticated user (staff, delivery, or customer login)
authenticated_urlpatterns = [
    path("", index, name="home"),
    path("logout/", sign_out, name="logout"),
    path("profile/", profile_user, name="profile_user"),
    path("profile/update", update_profile, name="update_profile"),
    path("profile/emails/update", update_profile_emails, name="update_profile_emails"),
]

staff_urlpatterns = decorate_urlpatterns(staff_urlpatterns, is_staff)
delivery_urlpatterns = decorate_urlpatterns(delivery_urlpatterns, is_delivery)
customer_urlpatterns = decorate_urlpatterns(customer_urlpatterns, is_customer)
authenticated_urlpatterns = decorate_urlpatterns(authenticated_urlpatterns, login_required)
_tag_access_tier(public_urlpatterns, "public")
_tag_access_tier(authenticated_urlpatterns, "authenticated")

urlpatterns = [
    path("admin/", admin.site.urls),
] + public_urlpatterns + authenticated_urlpatterns + delivery_urlpatterns + staff_urlpatterns + customer_urlpatterns
