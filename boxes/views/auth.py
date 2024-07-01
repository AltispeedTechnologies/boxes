# Authentication-related view classes
# Register, sign in, and sign out

import logging
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from boxes.forms import RegisterForm
from boxes.management.exception_catcher import exception_catcher
from boxes.models import CustomUser


@csrf_exempt
@exception_catcher()
def sign_in(request):
    if request.method == "GET":
        return render(request, "login.html", {"form": AuthenticationForm()})

    elif request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        next_page = request.POST.get("next", None)

        user = CustomUser.objects.only("id", "password", "is_active").get(username=username)

        if check_password(password, user.password):
            if user.is_active:
                login(request, user)
                if next_page:
                    return redirect(next_page)
                else:
                    success = reverse_lazy("home")
                    return redirect(success)
            else:
                messages.error(request, "Your account is not active.")
        else:
            messages.error(request, "Invalid username or password")

        return render(request, "login.html", {"form": AuthenticationForm()})


def sign_out(request):
    logout(request)
    messages.success(request, f"You have been logged out.")
    return redirect("home")
