"""ReportLab package label generation."""
import os
import re
from boxes.models import GlobalSettings, Package
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics


def _fit_font_size(text, font_name, font_size, max_width, min_font_size=8):
    """Shrink font until text fits within max_width or min size is reached."""
    size = font_size
    while size > min_font_size and pdfmetrics.stringWidth(text, font_name, size) >= max_width:
        size -= 1
    return size


def _split_text_for_width(text, font_name, font_size, max_width):
    """Split text into up to two lines that fit max_width (prefer space break)."""
    if pdfmetrics.stringWidth(text, font_name, font_size) < max_width:
        return [text]

    # Prefer breaking on whitespace near the midpoint
    mid = len(text) // 2
    best = None
    for i, ch in enumerate(text):
        if ch.isspace():
            if best is None or abs(i - mid) < abs(best - mid):
                best = i
    if best is not None and best > 0:
        line1 = text[:best].rstrip()
        line2 = text[best:].lstrip()
        if line1 and line2:
            return [line1, line2]

    # Hard split when there is no usable space
    for i in range(len(text) - 1, 0, -1):
        if pdfmetrics.stringWidth(text[:i], font_name, font_size) < max_width:
            return [text[:i], text[i:]]
    return [text]


def draw_centered_string(canvas_obj, y, text, font_name, font_size, page_width, wrap=False):
    """Draw a centered string; optionally wrap long names onto a second line.

    Never truncates with ellipsis — shrinks font and/or wraps instead.
    """
    max_width = page_width - inch
    if not wrap:
        font_size = _fit_font_size(text, font_name, font_size, max_width)
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        x = (page_width - text_width) / 2.0
        canvas_obj.setFont(font_name, font_size)
        canvas_obj.drawString(x, y, text)
        return

    # Name fields: shrink first, then wrap to a second line if still too wide
    min_size = 12 if font_size >= 30 else 10
    size = _fit_font_size(text, font_name, font_size, max_width, min_font_size=min_size)
    if pdfmetrics.stringWidth(text, font_name, size) < max_width:
        text_width = pdfmetrics.stringWidth(text, font_name, size)
        x = (page_width - text_width) / 2.0
        canvas_obj.setFont(font_name, size)
        canvas_obj.drawString(x, y, text)
        return

    # Still too wide at min size — wrap onto two lines and re-fit each
    lines = _split_text_for_width(text, font_name, size, max_width)
    if len(lines) == 1:
        size = _fit_font_size(lines[0], font_name, size, max_width, min_font_size=8)
        text_width = pdfmetrics.stringWidth(lines[0], font_name, size)
        x = (page_width - text_width) / 2.0
        canvas_obj.setFont(font_name, size)
        canvas_obj.drawString(x, y, lines[0])
        return

    line_gap = size * 1.15
    # Second line sits lower; first line slightly above the original y
    positions = [y + line_gap * 0.35, y - line_gap * 0.65]
    for line, line_y in zip(lines, positions):
        line_size = _fit_font_size(line, font_name, size, max_width, min_font_size=8)
        text_width = pdfmetrics.stringWidth(line, font_name, line_size)
        x = (page_width - text_width) / 2.0
        canvas_obj.setFont(font_name, line_size)
        canvas_obj.drawString(x, line_y, line)


def draw_label(canvas_obj, first_name, last_name, barcode_value, date, inside):
    """Draw one label onto a ReportLab canvas."""
    page_width, page_height = 4*inch, 6*inch

    def draw_centered(y, text, font_name, font_size, wrap=False):
        draw_centered_string(canvas_obj, y, text, font_name, font_size, page_width, wrap=wrap)

    globalsettings = GlobalSettings.load()

    # Draw the fixed information
    if inside:
        draw_centered(2.75*inch, globalsettings.name, "Helvetica-Bold", 18)
        draw_centered(2.5*inch, globalsettings.address1, "Helvetica-Bold", 12)
        draw_centered(2.25*inch, globalsettings.address2, "Helvetica-Bold", 12)
        draw_centered(2.0*inch, globalsettings.website, "Helvetica-Bold", 12)
        draw_centered(1.75*inch, globalsettings.email, "Helvetica-Bold", 12)
        draw_centered(1.5*inch, globalsettings.phone_number, "Helvetica-Bold", 12)
    else:
        draw_centered(2.85*inch, globalsettings.name, "Helvetica-Bold", 18)
        draw_centered(2.6*inch, globalsettings.address1, "Helvetica-Bold", 12)
        draw_centered(2.35*inch, globalsettings.address2, "Helvetica-Bold", 12)
        draw_centered(2.1*inch, globalsettings.website, "Helvetica-Bold", 12)
        draw_centered(1.85*inch, globalsettings.email, "Helvetica-Bold", 12)
        draw_centered(1.6*inch, globalsettings.phone_number, "Helvetica-Bold", 12)

    # Draw the variable information (names wrap/shrink; no ellipsis)
    draw_centered(5.4*inch, first_name, "Helvetica", 24, wrap=True)
    draw_centered(4.8*inch, last_name, "Helvetica-Bold", 40, wrap=True)
    draw_centered(0.2*inch, date, "Helvetica", 10)
    if inside:
        draw_centered(3.15*inch, "Climate Controlled", "Helvetica-Bold", 22)
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
    barcode.drawOn(canvas_obj, (page_width - barcode_width) / 2.0, barcode_y)
    draw_centered(barcode_y_string, barcode_value, "Helvetica", 10)

    # Draw the logo
    logo_path = os.path.join(settings.MEDIA_ROOT, "images/label_logo.png")
    canvas_obj.drawImage(logo_path, (page_width - 1*inch) / 2, 0.4*inch, width=1*inch, height=1*inch, mask="auto")


def get_ids(request):
    """Parse package ids from the request for label printing."""
    ids = request.GET.get("ids")
    if ids:
        ids = re.sub(r"[^\d,]", "", ids)
        ids = ids.split(",")

    return ids


def generate_label(request):
    """GET: stream multi-label PDF for requested packages."""
    ids = get_ids(request)
    if not ids:
        return HttpResponse("No IDs provided.", content_type="text/plain", status=400)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename='label.pdf'"
    response["X-Frame-Options"] = "SAMEORIGIN"

    p = canvas.Canvas(response, pagesize=(4*inch, 6*inch))
    packages = Package.objects.filter(
        id__in=ids).select_related(
        "account").values_list(
        "account__name", "tracking_code", "inside")

    label_date = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %I:%M:%S %p")
    for desc, tracking, inside in packages:
        first_name, last_name = desc.split(" ", 1) if " " in desc else ("", desc)
        draw_label(p, first_name, last_name, tracking, label_date, inside)
        p.showPage()

    # Close the PDF object cleanly
    p.save()

    return response


def show_label(request):
    """GET: label print UI."""
    ids = get_ids(request)

    if not ids:
        return HttpResponse("No IDs provided.", content_type="text/plain", status=400)

    return render(request, "labels.html", {"ids": ids})
