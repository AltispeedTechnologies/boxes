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
from boxes.models import CustomUser


def register(request):
    # Simple page viewing
    if request.method == "GET":
        form = RegisterForm()
        return render(request, "register.html", {"form": form})

    # On submission of the form
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, "User successfully registered.")
            login(request, user)

            success = reverse_lazy("home")
            return redirect(success)
        else:
            # Also returns a message on the screen
            return render(request, "register.html", {"form": form})


@csrf_exempt
def sign_in(request):
    if request.method == "GET":
        return render(request, "login.html", {"form": AuthenticationForm()})

    elif request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            user = CustomUser.objects.only("id", "password", "is_active").get(username=username)

            if check_password(password, user.password):
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Hi {username.title()}, welcome back!")
                    success = reverse_lazy("home")
                    return redirect(success)
                else:
                    messages.error(request, "Your account is not active.")
            else:
                messages.error(request, "Invalid username or password")

        except CustomUser.DoesNotExist:
            messages.error(request, f"User not found with username: {username}")

        return render(request, "login.html", {"form": AuthenticationForm()})


def sign_out(request):
    logout(request)
    messages.success(request, f"You have been logged out.")
    return redirect("home")
