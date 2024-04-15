from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.urls import path
from .views import *

def is_staff(view_func):
    return login_required(user_passes_test(is_staff, login_url=HttpResponseForbidden)(view_func))

urlpatterns = [
    path("", index, name="home"),

    # User authentication
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),

    # Backend endpoints
    path("accounts/search/", is_staff(account_search), name="account_search"),
    path("carriers/search/", is_staff(carrier_search), name="carrier_search"),

    # Generic package information
    path("packages/", is_staff(all_packages), name="packages"),
    path("packages/<int:pk>", is_staff(package_detail), name="package_detail"),

    # Search page
    path("packages/search", is_staff(search_packages), name="search_packages"),

    # Check in page
    path("packages/checkin", is_staff(check_in_packages), name="check_in_packages"),
    path("packages/new", is_staff(create_package), name="create_package"),

    # Check out page
    path("packages/checkout", is_staff(check_out_packages), name="check_out_packages"),
    path("packages/checkout/search", is_staff(search_check_out_packages), name="search_check_out_packages"),

    # Picklists page
    path("packages/picklists", is_staff(picklists), name="picklists"),
    path("packages/picklists/<int:pk>", is_staff(picklist_show), name="picklist_show"),
    path("packages/picklists/add", is_staff(add_package_picklist), name="add_package_picklist"),
    path("packages/picklists/move", is_staff(move_package_picklist), name="move_package_picklist"),
    path("packages/picklists/remove", is_staff(remove_package_picklist), name="remove_package_picklist"),
    path("packages/picklists/search", is_staff(search_picklist_packages), name="search_picklist_packages"),

    # Label printing
    path("packages/label", is_staff(generate_label), name="generate_label"),
]
