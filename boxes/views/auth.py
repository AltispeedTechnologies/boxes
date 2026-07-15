"""Session login and logout views."""
# Authentication-related view classes
# Register, sign in, and sign out

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect


def sign_in(request):
    """Render login form or authenticate and redirect (honors ``next``)."""
    if request.method == "GET":
        return render(request, "login.html", {"form": AuthenticationForm()})

    form = AuthenticationForm(request, data=request.POST)
    next_page = request.POST.get("next") or None

    if form.is_valid():
        user = form.get_user()
        login(request, user)
        if next_page:
            return redirect(next_page)
        return redirect("home")

    # Prefer a single clear message when credentials fail
    if not form.non_field_errors() and form.errors:
        messages.error(request, "Invalid username or password")
    for error in form.non_field_errors():
        messages.error(request, error)

    return render(request, "login.html", {"form": form})


def sign_out(request):
    """Log out the current user and redirect to the login page (full document)."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")
