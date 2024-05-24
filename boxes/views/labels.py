import datetime
import os
import pytz
import re
from boxes.models import *
from django.conf import settings
from django.http import HttpResponse
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics


def draw_label(canvas, first_name, last_name, barcode_value, date, inside):
    page_width, page_height = 4*inch, 6*inch

    def draw_centered_string(y, text, font_name, font_size):
        if len(text) > 13 and font_size > 24:
            text = text[:10] + "..."
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        while text_width >= (page_width - inch):
            font_size -= 1
            text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        x = (page_width - text_width) / 2.0
        canvas.setFont(font_name, font_size)
        canvas.drawString(x, y, text)

    # Draw the fixed information
    if inside:
        draw_centered_string(2.75*inch, "Mike's Parcel", "Helvetica-Bold", 18)
        draw_centered_string(2.5*inch, "373 W Stutsman Street", "Helvetica-Bold", 12)
        draw_centered_string(2.25*inch, "Pembina, ND 58271", "Helvetica-Bold", 12)
        draw_centered_string(2.0*inch, "www.mikesparcelpickup.com", "Helvetica-Bold", 12)
        draw_centered_string(1.75*inch, "mikesparcelpickup@gmail.com", "Helvetica-Bold", 12)
        draw_centered_string(1.5*inch, "701-825-6471", "Helvetica-Bold", 12)
    else:
        draw_centered_string(2.85*inch, "Mike's Parcel", "Helvetica-Bold", 18)
        draw_centered_string(2.6*inch, "373 W Stutsman Street", "Helvetica-Bold", 12)
        draw_centered_string(2.35*inch, "Pembina, ND 58271", "Helvetica-Bold", 12)
        draw_centered_string(2.1*inch, "www.mikesparcelpickup.com", "Helvetica-Bold", 12)
        draw_centered_string(1.85*inch, "mikesparcelpickup@gmail.com", "Helvetica-Bold", 12)
        draw_centered_string(1.6*inch, "701-825-6471", "Helvetica-Bold", 12)

    # Draw the variable information
    draw_centered_string(5.4*inch, first_name, "Helvetica", 24)
    draw_centered_string(4.8*inch, last_name, "Helvetica-Bold", 40)
    draw_centered_string(0.2*inch, date, "Helvetica", 10)
    if inside:
        draw_centered_string(3.15*inch, "Climate Controlled", "Helvetica-Bold", 22)
        barcode_y = 3.75 * inch
        barcode_y_string = 3.55 * inch
        barcode_height = 0.75 * inch
    else:
        barcode_y = 3.45 * inch
        barcode_y_string = 3.25 * inch
        barcode_height = 1 * inch

    # Draw the barcode
    barcode = createBarcodeDrawing("Code128", value=barcode_value, barWidth=0.9, barHeight=barcode_height,
                                   humanReadable=False)
    barcode_width = barcode.width
    barcode.drawOn(canvas, (page_width - barcode_width) / 2.0, barcode_y)
    draw_centered_string(barcode_y_string, barcode_value, "Helvetica", 10)

    # Draw the logo
    logo_path = os.path.join(settings.STATIC_ROOT, "img/logo.png")
    canvas.drawImage(logo_path, (page_width - 1*inch) / 2, 0.4*inch, width=1*inch, height=1*inch, mask="auto")


def generate_label(request):
    ids = request.GET.get("ids")
    if ids:
        ids = re.sub(r"[^\d,]", "", ids)
        ids = ids.split(",")
    else:
        return HttpResponse("No IDs provided.", content_type="text/plain", status=400)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename='label.pdf'"

    p = canvas.Canvas(response, pagesize=(4*inch, 6*inch))
    packages = Package.objects.filter(
        id__in=ids).select_related(
        "account").values_list(
        "account__name", "tracking_code", "inside")

    central_timezone = pytz.timezone("America/Chicago")
    now_utc = datetime.datetime.now(pytz.utc)
    now_central = now_utc.astimezone(central_timezone)
    label_date = now_central.strftime("%Y-%m-%d %I:%M:%S %p")
    for desc, tracking, inside in packages:
        first_name, last_name = desc.split(" ", 1) if " " in desc else ("", desc)
        draw_label(p, first_name, last_name, tracking, label_date, inside)
        p.showPage()

    # Close the PDF object cleanly
    p.save()

    return response
