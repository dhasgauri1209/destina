from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def create_itinerary_pdf(trip, itinerary):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 20 * mm

    def draw_line(text, font_name="Helvetica", font_size=11, gap=7 * mm):
        nonlocal y
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
        pdf.setFont(font_name, font_size)
        pdf.drawString(18 * mm, y, text)
        y -= gap

    draw_line("Destina - Travel Itinerary", "Helvetica-Bold", 16, gap=10 * mm)
    draw_line(f"Destination: {trip.destination}")
    draw_line(f"Trip Duration: {trip.days} days")
    draw_line(f"Budget: INR {trip.budget:,.2f}")
    draw_line(f"Estimated Total Cost: INR {trip.total_cost:,.2f}")
    draw_line("", gap=3 * mm)

    for day in itinerary:
        draw_line(day["title"], "Helvetica-Bold", 12)
        draw_line(f"Morning: {day['morning']}")
        draw_line(f"Afternoon: {day['afternoon']}")
        draw_line(f"Evening: {day['evening']}")
        draw_line("", gap=3 * mm)

    pdf.save()
    buffer.seek(0)
    return buffer
