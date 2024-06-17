from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.urls import include, path
from boxes.views import *
from boxes.views.mgmt import *
from boxes.views.packages import *


def is_staff(view_func):
    return login_required(user_passes_test(is_staff, login_url=HttpResponseForbidden)(view_func))


urlpatterns = [
    path("", index, name="home"),
    path("admin/", admin.site.urls),

    # User authentication
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),

    # Management dropdown
    path("mgmt/charges", is_staff(charge_settings), name="charge_settings"),
    path("mgmt/charges/update", is_staff(save_charge_settings), name="save_charge_settings"),
    path("mgmt/email/configure", is_staff(email_settings), name="email_settings"),
    path("mgmt/email/logs", is_staff(email_logs), name="email_logs"),
    path("mgmt/email/update", is_staff(save_email_settings), name="save_email_settings"),
    path("mgmt/email/templates", is_staff(email_template), name="email_template"),
    path("mgmt/email/templates/add", is_staff(add_email_template), name="add_email_template"),
    path("mgmt/email/templates/fetch", is_staff(email_template_content), name="email_template_content"),
    path("mgmt/email/templates/update", is_staff(update_email_template), name="update_email_template"),
    path("mgmt/general", is_staff(general_settings), name="general_settings"),
    path("mgmt/general/update", is_staff(save_general_settings), name="save_general_settings"),
    path("mgmt/packages/carriers", is_staff(carrier_settings), name="carrier_settings"),
    path("mgmt/packages/carriers/update", is_staff(update_carriers), name="update_carriers"),
    path("mgmt/packages/types", is_staff(package_type_settings), name="package_type_settings"),
    path("mgmt/packages/types/update", is_staff(update_package_types), name="update_package_types"),

    # Accounts
    path("accounts/<int:pk>/edit", is_staff(account_edit), name="account_edit"),
    path("accounts/<int:pk>/emails", is_staff(account_emails), name="account_emails"),
    path("accounts/<int:pk>/ledger", is_staff(account_ledger), name="account_ledger"),
    path("accounts/<int:pk>/packages", is_staff(account_packages), name="account_packages"),
    path("accounts/<int:pk>/update", is_staff(update_account), name="update_account"),
    path("accounts/aliases/update", is_staff(update_account_aliases), name="update_account_aliases"),
    path("accounts/search", is_staff(account_search), name="account_search"),

    # Backend endpoints
    path("carriers/search", is_staff(carrier_search), name="carrier_search"),
    path("emails/<int:pk>/contents", is_staff(get_email_contents), name="get_email_contents"),
    path("picklists/query", is_staff(picklist_query), name="picklist_query"),
    path("types/search", is_staff(type_search), name="type_search"),
    path("modals/bulk", is_staff(get_bulk_modals), name="get_bulk_modals"),
    path("modals/actions", is_staff(get_actions_modals), name="get_actions_modals"),
    path("modals/picklistmgmt", is_staff(get_picklist_mgmt_modals), name="get_picklist_mgmt_modals"),

    # Generic package information
    path("packages/", is_staff(all_packages), name="packages"),
    path("packages/<int:pk>", is_staff(package_detail), name="package_detail"),
    path("packages/<int:pk>/update", is_staff(update_package), name="update_package"),
    path("packages/update", is_staff(update_packages), name="update_packages"),

    # Search page
    path("packages/search", is_staff(search_packages), name="search_packages"),

    # Check in page
    path("packages/checkin", is_staff(check_in), name="check_in"),
    path("packages/checkin/create", is_staff(create_package), name="create_package"),
    path("packages/checkin/submit", is_staff(check_in_packages), name="check_in_packages"),

    # Check out page
    path("packages/checkout", is_staff(check_out), name="check_out"),
    path("packages/checkout/submit", is_staff(check_out_packages), name="check_out_packages"),
    path("packages/checkout/reverse", is_staff(check_out_packages_reverse), name="check_out_packages_reverse"),
    path("packages/checkout/verify", is_staff(verify_can_checkout), name="verify_can_checkout"),

    # Picklists page
    path("picklists/", is_staff(picklist_list), name="picklists"),
    path("picklists/<int:pk>/checkout", is_staff(picklist_check_out), name="picklist_check_out"),
    path("picklists/<int:pk>/packages", is_staff(picklist_show), name="picklist_show"),
    path("picklists/<int:pk>/remove", is_staff(remove_picklist), name="remove_picklist"),
    path("picklists/create", is_staff(create_picklist), name="create_picklist"),
    path("picklists/modify", is_staff(modify_package_picklist), name="modify_package_picklist"),
    path("picklists/remove", is_staff(remove_package_picklist), name="remove_package_picklist"),

    # Label printing
    path("packages/label", is_staff(show_label), name="show_label"),
    path("packages/label/pdf", is_staff(generate_label), name="generate_label"),

    # Basic queue data
    path("queues/<int:pk>/packages", is_staff(queue_packages), name="queue_packages"),
    path("queues/<int:pk>/update", is_staff(update_queue_name), name="update_queue_name"),

    # Users
    path("users/new", is_staff(create_user), name="create_user"),
    path("users/update", is_staff(update_user), name="update_user"),
    path("users/emails/update", is_staff(update_user_emails), name="update_user_emails"),

    # Reports
    path("reports/", is_staff(reports), name="reports"),
    path("reports/name", is_staff(report_name_search), name="report_name_search"),
    path("reports/new", is_staff(report_details), name="report_new"),
    path("reports/new/submit", is_staff(report_new_submit), name="report_new_submit"),
    path("reports/<int:pk>/edit", is_staff(report_details), name="report_details"),
    path("reports/<int:pk>/remove", is_staff(report_remove), name="report_remove"),
    path("reports/<int:pk>/update", is_staff(report_update), name="report_update"),
    path("reports/stats/chart", is_staff(report_stats_chart), name="report_stats_chart")
]
