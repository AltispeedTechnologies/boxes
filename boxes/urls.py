from django.urls import path
from boxes.views import *

urlpatterns = [
    path("", views.index, name="home"),
    path("register/", views.register, name="register"),
]
