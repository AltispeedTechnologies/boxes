"""Customer home page."""
from django.shortcuts import render


def index(request):
    """Render customer landing page."""
    return render(request, "index.html")
