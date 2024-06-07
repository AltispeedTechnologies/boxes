import json
from boxes.management.exception_catcher import exception_catcher
from boxes.models import GlobalSettings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from io import BytesIO
from PIL import Image


@require_http_methods(["GET"])
def general_settings(request):
    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    return render(request, "mgmt/general.html", {"settings": settings})


@require_http_methods(["POST"])
@exception_catcher()
def save_general_settings(request):
    settings, _ = GlobalSettings.objects.get_or_create(id=1)

    payload = request.POST.get("payload")
    if payload:
        payload = json.loads(payload)
        for key, value in payload.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    logo = request.FILES.get("image")
    if logo and logo.name.endswith(".png"):
        # Save the source image
        settings.source_image.save("logo.png", ContentFile(logo.read()), save=False)
        logo.seek(0)  # Rewind to the beginning of the file after reading

        image = Image.open(logo)

        # Process and save various resized images
        resize_and_save(image, (40, 40), "PNG", settings, "navbar_image", "navbar_logo.png")
        resize_and_save(image, (100, 100), "PNG", settings, "label_image", "label_logo.png")
        resize_and_save(image, (64, 64), "PNG", settings, "login_image", "login_logo.png")

        # Special case for favicon with multiple sizes
        favicon_buffer = BytesIO()
        sizes = [(16, 16), (32, 32), (48, 48)]
        favicon = image.resize((48, 48), Image.Resampling.LANCZOS)
        favicon.save(favicon_buffer, format="ICO", sizes=sizes)
        settings.favicon_image.save("favicon.ico", ContentFile(favicon_buffer.getvalue()), save=False)
    elif logo:
        return JsonResponse({"success": False, "errors": "Invalid PNG image"})

    # Save the settings instance
    settings.save()


# Utility function for resizing and saving images
def resize_and_save(image, size, format, model, attribute, filename):
    # Resize the image
    resized_image = image.resize(size, Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = BytesIO()
    resized_image.save(buffer, format=format)
    buffer_content = buffer.getvalue()

    # Save the image to the specified model field
    getattr(model, attribute).save(filename, ContentFile(buffer_content), save=False)
