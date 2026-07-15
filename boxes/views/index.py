"""Site home page."""
from django.shortcuts import redirect, render


def index(request):
    """Render customer home, or send staff-only users to packages.

    Users in the Customer group keep the customer landing page. Authenticated
    staff without Customer membership are redirected to the staff package list.
    """
    user = request.user
    if user.is_authenticated and user.has_staff_role() and not user.is_customer():
        return redirect("packages")
    return render(request, "index.html")
