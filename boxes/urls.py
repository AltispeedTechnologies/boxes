from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import *

urlpatterns = [
    path("", index, name="home"),
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),

    path("packages/", all_packages, name="packages"),
    path("packages/new", create_package, name="create_package"),
    path("packages/search", search_packages, name="search_packages"),
]
