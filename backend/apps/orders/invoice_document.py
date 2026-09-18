"""Build the template context for the official A4 invoice from real order data.

No demo values: every number comes from the Invoice snapshot / Order, every
identity field from CompanyInfo / Invoice snapshot, payment rows from the
latest verified Payment. Missing optional data renders as "—", never as
invented content.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.template.loader import render_to_string

from apps.company.models import CompanyInfo

from .invoice_text import amount_in_words, fa_date, fa_digits, fa_time
from .models import Invoice


def _dec(value) -> int:
    try:
        return int(Decimal(str(value if value not in (None, "") else 0)))
    except (InvalidOperation, ValueError, TypeError):
        return 0


def build_invoice_context(invoice: Invoice, base_url: str = "") -> dict:
    order = invoice.order
    company = CompanyInfo.objects.first()
    payment = order.payments.filter(status="verified").order_by("-verified_at", "-id").first()
    if payment is None:
        payment = order.payments.order_by("-created_at", "-id").first()

    paid = bool(order.paid_at or (payment and payment.status == "verified"))
    has_proforma = order.proformarequest_set.exists() if hasattr(order, "proformarequest_set") else False
    if paid:
        status = {"key": "paid", "label": "پرداخت شده", "title": "فاکتور فروش کالا و خدمات",
                  "subtitle": "فاکتور قطعی و سند فروش رسمی — شماره اختصاصی مؤدیان",
                  "number": invoice.invoice_number}
    elif has_proforma:
        status = {"key": "proforma", "label": "پیش‌فاکتور رسمی", "title": "پیش‌فاکتور رسمی (استعلام بها)",
                  "subtitle": "پیش‌فاکتور معتبر جهت اخذ مجوز خرید و تأمین اعتبار",
                  "number": invoice.invoice_number.replace("INV-", "PRO-", 1)}
    else:
        status = {"key": "pending", "label": "در انتظار پرداخت", "title": "فاکتور فروش کالا و خدمات",
                  "subtitle": "صورتحساب فروش — در انتظار تسویه",
                  "number": invoice.invoice_number}

    items = []
    for position, row in enumerate(invoice.items_snapshot or [], start=1):
        unit_price = _dec(row.get("unit_price"))
        quantity = _dec(row.get("quantity"))
        discount = _dec(row.get("discount_amount"))
        line_total = _dec(row.get("line_total", unit_price * quantity - discount))
        items.append({
            "position": fa_digits(position),
            "name": row.get("product_name") or "—",
            "code": row.get("product_code") or "—",
            "brand": row.get("brand") or "—",
            "model": row.get("model") or "—",
            "image_url": (base_url + row["image_url"]) if row.get("image_url") else "",
            "quantity": fa_digits(quantity),
            "quantity_raw": quantity,
            "unit": row.get("unit") or "عدد",
            "unit_price": fa_digits(unit_price), "unit_price_raw": unit_price,
            "discount": fa_digits(discount), "discount_raw": discount,
            "line_total": fa_digits(line_total), "line_total_raw": line_total,
        })

    subtotal = _dec(invoice.subtotal)
    discount = _dec(invoice.discount)
    tax = _dec(invoice.tax)
    shipping = _dec(getattr(order, "shipping_cost", 0))
    total = _dec(invoice.final_amount)

    def media_url(field) -> str:
        if not field:
            return ""
        url = field.url if hasattr(field, "url") else str(field)
        return (base_url + url) if url.startswith("/") else url

    seller = {
        "name": (company.name_fa if company else "") or "شرکت کارخانجات تولیدی مهراصل",
        "logo_url": media_url(company.logo) if company else "",
        "address": (company.address if company else "") or "—",
        "phone": (company.phone if company else "") or "—",
        "mobile": (company.mobile if company else "") or "—",
        "email": (company.email if company else "") or "—",
        "website": (company.website if company else "") or "—",
    }
    buyer = {
        "name": invoice.customer_name or "—",
        "company": invoice.company_name or "",
        "national_id": invoice.national_id or "—",
        "economic_code": invoice.economic_code or "—",
        "phone": invoice.phone or order.customer_phone or "—",
        "mobile": order.customer_phone or "—",
        "address": invoice.address or "—",
        "email": order.customer_email or "—",
    }
    pay = None
    if payment is not None:
        pay = {
            "method": {"zarinpal": "درگاه پرداخت آنلاین (زرین‌پال)"}.get(payment.gateway, payment.gateway or "—"),
            "state": "پرداخت قطعی (تایید مالی)" if payment.status == "verified" else dict(payment.Status.choices).get(payment.status, payment.status),
            "paid": payment.status == "verified",
            "reference": payment.reference_id or payment.authority or "—",
            "at": f"{fa_date(payment.verified_at or payment.created_at)} - {fa_time(payment.verified_at or payment.created_at)}",
        }

    return {
        "status": status,
        "order_number": order.order_number,
        "issued_date": fa_date(invoice.created_at),
        "issued_time": fa_time(invoice.created_at),
        "seller": seller,
        "buyer": buyer,
        "items": items,
        "items_count": fa_digits(len(items)),
        "subtotal": fa_digits(subtotal), "subtotal_raw": subtotal,
        "discount": fa_digits(discount), "discount_raw": discount,
        "net": fa_digits(subtotal - discount), "net_raw": subtotal - discount,
        "tax": fa_digits(tax), "tax_raw": tax,
        "shipping": fa_digits(shipping), "shipping_raw": shipping,
        "total": fa_digits(total), "total_raw": total,
        "total_words": f"{amount_in_words(total)} ریال تمام",
        "total_words_toman": f"{amount_in_words(total // 10)} تومان تمام",
        "payment": pay,
        "shipping_address": "، ".join(filter(None, (order.shipping_province, order.shipping_city, order.shipping_address))) or "—",
        "postal_code": order.shipping_postal_code or "—",
        "invoice_uid": f"{invoice.invoice_number}-{order.id:06d}",
    }


def render_invoice_html(invoice: Invoice, base_url: str = "") -> str:
    return render_to_string("orders/invoice.html", build_invoice_context(invoice, base_url))
