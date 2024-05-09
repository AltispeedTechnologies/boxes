from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.urls import include, path
from .views import *

def is_staff(view_func):
    return login_required(user_passes_test(is_staff, login_url=HttpResponseForbidden)(view_func))

urlpatterns = [
    path("", index, name="home"),

    # User authentication
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),

    # Management dropdown
    path("mgmt/charges", is_staff(charge_settings), name="charge_settings"),
    path("mgmt/charges/update", is_staff(save_charge_settings), name="save_charge_settings"),
    path("mgmt/email", is_staff(email_settings), name="email_settings"),
    path("mgmt/email/update", is_staff(save_email_settings), name="save_email_settings"),
    path("mgmt/email/templates", is_staff(email_template), name="email_template"),
    path("mgmt/email/templates/add", is_staff(add_email_template), name="add_email_template"),
    path("mgmt/email/templates/fetch", is_staff(email_template_content), name="email_template_content"),
    path("mgmt/email/templates/update", is_staff(update_email_template), name="update_email_template"),

    # Accounts
    path("accounts/<int:pk>/edit", is_staff(account_edit), name="account_edit"),
    path("accounts/<int:pk>/ledger", is_staff(account_ledger), name="account_ledger"),
    path("accounts/<int:pk>/packages", is_staff(account_packages), name="account_packages"),
    path("accounts/<int:pk>/update", is_staff(update_account), name="update_account"),
    path("accounts/aliases/update", is_staff(update_package_aliases), name="update_package_aliases"),
    path("accounts/search", is_staff(account_search), name="account_search"),

    # Backend endpoints
    path("carriers/search", is_staff(carrier_search), name="carrier_search"),
    path("picklists/query", is_staff(picklist_query), name="picklist_query"),
    path("types/search", is_staff(type_search), name="type_search"),
    path("packages/checkout", is_staff(check_out_packages), name="check_out_packages"),
    path("packages/checkout/reverse", is_staff(check_out_packages_reverse), name="check_out_packages_reverse"),
    path("modals/bulk", is_staff(get_bulk_modals), name="get_bulk_modals"),
    path("modals/actions", is_staff(get_actions_modals), name="get_actions_modals"),

    # Generic package information
    path("packages/", is_staff(all_packages), name="packages"),
    path("packages/<int:pk>", is_staff(package_detail), name="package_detail"),
    path("packages/<int:pk>/update", is_staff(update_package), name="update_package"),
    path("packages/update", is_staff(update_packages), name="update_packages"),

    # Search page
    path("packages/search", is_staff(search_packages), name="search_packages"),

    # Check in page
    path("packages/checkin", is_staff(check_in_packages), name="check_in_packages"),
    path("packages/new", is_staff(create_package), name="create_package"),

    # Picklists page
    path("packages/picklists", is_staff(picklist_show), name="picklists"),
    path("packages/picklists/<int:pk>", is_staff(picklist_show), name="picklist_show"),
    path("packages/picklists/modify", is_staff(modify_package_picklist), name="modify_package_picklist"),
    path("packages/picklists/remove", is_staff(remove_package_picklist), name="remove_package_picklist"),

    # Label printing
    path("packages/label", is_staff(generate_label), name="generate_label"),

    # Basic queue data
    path("queues/<int:pk>/packages", is_staff(queue_packages), name="queue_packages"),

    # Users
    path("users/update", is_staff(update_user), name="update_user"),
]
