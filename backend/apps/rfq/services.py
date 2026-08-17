import html
import io
from decimal import Decimal

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.company.models import CompanyInfo
from apps.common.document_typography import register_document_fonts
from apps.common.jalali import format_document_date

from .models import SalesQuotation


def _rtl(value):
    return get_display(arabic_reshaper.reshape(str(value)))


def _safe(value):
    return html.escape(str(value or "")).replace("\n", "<br/>")


def _register_font():
    return register_document_fonts()


def _money(value, currency, english):
    amount = f"{Decimal(value):,.2f}"
    if not english:
        amount = amount.translate(str.maketrans("0123456789,.", "۰۱۲۳۴۵۶۷۸۹٬٫"))
    return f"{amount} {currency}"


def generate_quotation_pdf(quotation, locale="fa"):
    english = locale == "en"
    font_names = _register_font()
    font_name = font_names["latin"] if english else font_names["persian"]
    medium_name = font_names["latin"] if english else font_names["persian_medium"]
    bold_name = font_names["latin"] if english else font_names["persian_bold"]
    latin_name = font_names["latin"]
    styles = getSampleStyleSheet()
    body = ParagraphStyle("quotation-body", parent=styles["Normal"], fontName=font_name, fontSize=8.5, leading=14, alignment=0 if english else TA_RIGHT)
    ltr_body = ParagraphStyle("quotation-ltr", parent=body, fontName=latin_name, alignment=0)
    title = ParagraphStyle("quotation-title", parent=body, fontName=bold_name, fontSize=17, leading=23, alignment=0 if english else TA_RIGHT)
    small = ParagraphStyle("quotation-small", parent=body, fontName=medium_name, fontSize=7.5, leading=11, textColor=colors.HexColor("#4b5563"))
    document = SimpleDocTemplate(io.BytesIO(), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    company = CompanyInfo.objects.order_by("id").first()
    rtl = not english
    def text(value, style=body):
        escaped = _safe(value)
        has_arabic = any("\u0600" <= character <= "\u06ff" for character in str(value or ""))
        if english and not has_arabic:
            style = ParagraphStyle(f"{style.name}-latin", parent=style, fontName=latin_name)
        return Paragraph(_rtl(escaped) if has_arabic else escaped, style)
    def ltr(value, style=ltr_body):
        return Paragraph(_safe(value), style)
    def label(fa, en):
        return text(en if english else fa)

    story = [text("Company Quotation" if english else "پیشنهاد قیمت شرکت", title), Spacer(1, 5 * mm)]
    company_name = company.name_fa if company else ""
    company_rows = []
    if company_name: company_rows.append([label("شرکت", "Company"), text(company_name)])
    if company and company.phone: company_rows.append([label("تلفن", "Phone"), text(company.phone)])
    if company and company.email: company_rows.append([label("ایمیل", "Email"), text(company.email)])
    if company and company.address: company_rows.append([label("نشانی", "Address"), text(company.address)])
    detail_rows = [
        [label("شناسه پیشنهاد", "Quotation reference"), ltr(quotation.reference)],
        [label("استعلام مرتبط", "Related RFQ"), ltr(quotation.rfq.reference)],
        [label("تاریخ صدور", "Issued"), text(format_document_date(quotation.issued_at, locale) if quotation.issued_at else "")],
    ]
    if quotation.expires_at:
        detail_rows.append([label("تاریخ انقضا", "Expires"), text(format_document_date(quotation.expires_at, locale))])
    if company_rows:
        company_table = Table(company_rows, colWidths=[35 * mm, 135 * mm])
        company_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#d1d5db")), ("PADDING", (0, 0), (-1, -1), 5)]))
        story += [company_table, Spacer(1, 4 * mm)]
    detail_table = Table(detail_rows, colWidths=[45 * mm, 125 * mm])
    detail_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#d1d5db")), ("PADDING", (0, 0), (-1, -1), 5)]))
    story += [detail_table, Spacer(1, 5 * mm), text("Customer" if english else "اطلاعات مشتری", title)]
    customer_rows = [[label("شرکت مشتری", "Customer company"), text(quotation.rfq.company_name or "-")], [label("نام تماس", "Contact"), text(quotation.rfq.contact_name)], [label("تلفن", "Phone"), ltr(quotation.rfq.phone or "-")], [label("ایمیل", "Email"), ltr(quotation.rfq.email or "-")]]
    customer_table = Table(customer_rows, colWidths=[45 * mm, 125 * mm])
    customer_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#d1d5db")), ("PADDING", (0, 0), (-1, -1), 5)]))
    story += [customer_table, Spacer(1, 6 * mm), text("Quoted items" if english else "اقلام پیشنهاد", title)]
    headers = ["Product", "Code", "Quantity", "Unit price", "Line total"] if english else ["محصول", "کد", "تعداد", "قیمت واحد", "جمع قلم"]
    rows = [[text(item) for item in headers]]
    for item in quotation.items.all():
        rows.append([text(item.product_name_snapshot), ltr(item.product_code_snapshot), ltr(item.quantity), ltr(_money(item.unit_price, quotation.currency, english)), ltr(_money(item.line_total, quotation.currency, english))])
    items_table = Table(rows, colWidths=[58 * mm, 30 * mm, 20 * mm, 31 * mm, 31 * mm], repeatRows=1)
    items_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font_name), ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#9ca3af")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 5)]))
    story += [items_table, Spacer(1, 5 * mm), text(f"Subtotal: {_money(quotation.subtotal, quotation.currency, english)}" if english else f"جمع اقلام: {_money(quotation.subtotal, quotation.currency, english)}", title)]
    if quotation.public_note:
        story += [Spacer(1, 3 * mm), text("Note" if english else "یادداشت", title), text(quotation.public_note)]
    story += [Spacer(1, 8 * mm), text("This document contains only the issued quotation data." if english else "این سند فقط شامل اطلاعات پیشنهاد قیمت صادرشده است.", small)]
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    document.build(story)
    return output.getvalue()
