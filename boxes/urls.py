from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import index, register
from .views.auth import sign_in, sign_out


urlpatterns = [
    path("", index, name="home"),
    path("register/", register, name="register"),
    path("login/", sign_in, name="login"),
    path("logout/", sign_out, name="logout"),
]
