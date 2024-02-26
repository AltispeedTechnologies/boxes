from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.urls import path
from .views import *

def is_staff(view_func):
    return login_required(user_passes_test(is_staff, login_url=HttpResponseForbidden)(view_func))

urlpatterns = [
    path("", index, name="home"),
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),

    path("packages/", is_staff(all_packages), name="packages"),
    path("packages/new", is_staff(create_package), name="create_package"),
    path("packages/checkin", is_staff(check_in_packages), name="check_in_packages"),
    path("packages/search", is_staff(search_packages), name="search_packages"),
]
