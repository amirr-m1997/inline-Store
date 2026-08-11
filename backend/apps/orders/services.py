import io
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Invoice, InvoiceEmailLog


def create_invoice(order):
    user = order.customer
    customer_name = " ".join(filter(None, (order.customer_first_name, order.customer_last_name))).strip()
    snapshot = [{
        "product_name": item.product_name, "product_code": item.product_code, "unit": item.unit,
        "unit_price": str(item.unit_price), "quantity": item.quantity,
        "discount_amount": str(item.discount_amount), "line_total": str(item.line_total),
    } for item in order.items.all()]
    invoice, _ = Invoice.objects.get_or_create(order=order, defaults={
        "invoice_number": f"INV-{order.order_number}",
        "company_name": order.customer_company_name,
        "customer_name": customer_name or order.customer_phone or "مشتری",
        "national_id": order.customer_national_id,
        "economic_code": getattr(user, "economic_code", "") if user else "",
        "phone": order.customer_phone,
        "address": "، ".join(filter(None, (order.shipping_province, order.shipping_city, order.shipping_address))),
        "items_snapshot": snapshot, "subtotal": order.subtotal, "tax": 0,
        "discount": order.discount_amount, "final_amount": order.final_amount,
    })
    return invoice


def _rtl(value):
    return get_display(arabic_reshaper.reshape(str(value)))


def ensure_invoice_pdf(invoice):
    if invoice.pdf_file:
        return invoice
    buffer = io.BytesIO()
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font_name = "DejaVu"
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    styles = getSampleStyleSheet()
    rtl = ParagraphStyle("rtl", parent=styles["Normal"], fontName=font_name, fontSize=9, leading=15, alignment=TA_RIGHT)
    title = ParagraphStyle("title-fa", parent=rtl, fontSize=16, leading=24)
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=14 * mm, bottomMargin=14 * mm)
    story = [Paragraph(_rtl("فاکتور فروش"), title), Spacer(1, 5 * mm)]
    details = [
        [_rtl(f"شماره فاکتور: {invoice.invoice_number}"), _rtl(f"شماره سفارش: {invoice.order.order_number}")],
        [_rtl(f"مشتری: {invoice.customer_name}"), _rtl(f"شرکت: {invoice.company_name or '-'}")],
        [_rtl(f"شناسه ملی: {invoice.national_id or '-'}"), _rtl(f"کد اقتصادی: {invoice.economic_code or '-'}")],
        [_rtl(f"تلفن: {invoice.phone or '-'}"), _rtl(f"نشانی: {invoice.address or '-'}")],
    ]
    table = Table(details, colWidths=[88 * mm, 88 * mm])
    table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("GRID", (0, 0), (-1, -1), .3, colors.grey), ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [table, Spacer(1, 5 * mm)]
    rows = [[_rtl("مبلغ"), _rtl("تعداد"), _rtl("واحد"), _rtl("کد"), _rtl("شرح")]]
    for item in invoice.items_snapshot:
        rows.append([str(item["line_total"]), str(item["quantity"]), _rtl(item["unit"]), item["product_code"], _rtl(item["product_name"])])
    items = Table(rows, colWidths=[32 * mm, 18 * mm, 24 * mm, 32 * mm, 70 * mm], repeatRows=1)
    items.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("FONTSIZE", (0, 0), (-1, -1), 8), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")), ("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("GRID", (0, 0), (-1, -1), .3, colors.grey), ("PADDING", (0, 0), (-1, -1), 5)]))
    story += [items, Spacer(1, 5 * mm), Paragraph(_rtl(f"جمع اقلام: {invoice.subtotal} ریال"), rtl), Paragraph(_rtl(f"تخفیف: {invoice.discount} ریال"), rtl), Paragraph(_rtl(f"مالیات: {invoice.tax} ریال"), rtl), Paragraph(_rtl(f"مبلغ نهایی: {invoice.final_amount} ریال"), title)]
    document.build(story)
    invoice.pdf_file.save(f"{invoice.invoice_number}.pdf", ContentFile(buffer.getvalue()), save=True)
    return invoice


def email_invoice(invoice, recipient):
    invoice = ensure_invoice_pdf(invoice)
    try:
        message = EmailMessage(subject=f"فاکتور سفارش {invoice.order.order_number}", body="فاکتور سفارش شما به پیوست ارسال شده است.", from_email=settings.DEFAULT_FROM_EMAIL, to=[recipient])
        message.attach(f"{invoice.invoice_number}.pdf", invoice.pdf_file.read(), "application/pdf")
        message.send(fail_silently=False)
        InvoiceEmailLog.objects.create(invoice=invoice, recipient=recipient, success=True)
    except Exception as exc:
        InvoiceEmailLog.objects.create(invoice=invoice, recipient=recipient, success=False, error_message=str(exc))
        raise
