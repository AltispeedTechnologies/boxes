"""Session login/logout and token-gated self-registration."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from boxes.backend.signup import complete_signup, get_valid_invite


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


@require_http_methods(["GET", "POST"])
def signup(request, token):
    """Public self-registration **only** via a valid staff-issued invite token.

    There is no open registration path without a token. Used/expired tokens
    show an error page; successful signup logs the user in and sends them home.
    """
    try:
        invite = get_valid_invite(token)
    except ValidationError as exc:
        errors = []
        if hasattr(exc, "message_dict"):
            for msgs in exc.message_dict.values():
                errors.extend(msgs)
        else:
            errors = list(exc.messages)
        return render(request, "signup.html", {
            "invalid": True,
            "errors": errors,
            "invite": None,
            "token": token,
        }, status=400)

    if request.method == "GET":
        return render(request, "signup.html", {
            "invalid": False,
            "invite": invite,
            "token": token,
            "form_errors": {},
            "form_data": {
                "username": "",
                "first_name": invite.first_name or "",
                "last_name": invite.last_name or "",
                "company": invite.company or "",
                "phone_number": invite.phone_number or "",
            },
        })

    form_data = {
        "username": (request.POST.get("username") or "").strip(),
        "first_name": (request.POST.get("first_name") or invite.first_name or "").strip(),
        "last_name": (request.POST.get("last_name") or invite.last_name or "").strip(),
        "company": (request.POST.get("company") or invite.company or "").strip(),
        "phone_number": (request.POST.get("phone_number") or invite.phone_number or "").strip(),
        "password1": request.POST.get("password1") or "",
        "password2": request.POST.get("password2") or "",
    }

    try:
        result = complete_signup(
            token=token,
            username=form_data["username"],
            password=form_data["password1"],
            password2=form_data["password2"],
            first_name=form_data["first_name"],
            last_name=form_data["last_name"],
            company=form_data["company"],
            phone_number=form_data["phone_number"],
        )
    except ValidationError as exc:
        form_errors = exc.message_dict if hasattr(exc, "message_dict") else {"non_field": list(exc.messages)}
        if "__all__" in form_errors:
            form_errors["non_field"] = form_errors.pop("__all__")
        # Normalize password field names for the template
        if "password" in form_errors and "password1" not in form_errors:
            form_errors["password1"] = form_errors.pop("password")
        return render(request, "signup.html", {
            "invalid": False,
            "invite": invite,
            "token": token,
            "form_errors": form_errors,
            "form_data": form_data,
        }, status=400)

    user = result["user"]
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "Your account is ready. Welcome!")
    return redirect("home")
