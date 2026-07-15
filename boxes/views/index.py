"""Site home page."""
from django.shortcuts import redirect, render


def index(request):
    """Render customer home, or send warehouse roles to packages/check-in.

    Users in the Customer group keep the customer landing page. Authenticated
    staff without Customer membership are redirected to the package list.
    Delivery-only users are redirected to check-in.
    """
    user = request.user
    if user.is_authenticated and user.has_staff_role() and not user.is_customer():
        return redirect("packages")
    if (
        user.is_authenticated
        and user.has_delivery_role()
        and not user.has_staff_role()
        and not user.is_customer()
    ):
        return redirect("check_in")
    return render(request, "index.html")
