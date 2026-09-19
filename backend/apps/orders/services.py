from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage

from .invoice_document import render_invoice_html
from .invoice_pdf import render_invoice_pdf_bytes
from .models import Invoice, InvoiceEmailLog


def _snapshot_image_url(product):
    if product is None:
        return ""
    image = product.images.order_by("-is_primary", "sort_order", "id").first()
    if not image or not image.image:
        return ""
    return image.image.url


def create_invoice(order):
    user = order.customer
    customer_name = " ".join(filter(None, (order.customer_first_name, order.customer_last_name))).strip()
    snapshot = []
    for item in order.items.select_related("product", "product__brand").all():
        product = item.product
        snapshot.append({
            "product_name": item.product_name, "product_code": item.product_code, "unit": item.unit,
            "unit_price": str(item.unit_price), "quantity": item.quantity,
            "discount_amount": str(item.discount_amount), "line_total": str(item.line_total),
            "brand": product.brand.name if product and product.brand else "",
            "image_url": _snapshot_image_url(product),
        })
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


CHROMIUM_RENDERER = "chromium-a4"


def ensure_invoice_pdf(invoice, base_url=""):
    """Store the official A4 PDF (re)built from the rich HTML invoice.

    Legacy reportlab PDFs (pdf_renderer == "") are regenerated on next
    download so customers always receive the official design.
    """
    if invoice.pdf_file and invoice.pdf_renderer == CHROMIUM_RENDERER:
        return invoice
    html = render_invoice_html(invoice, base_url or invoice_base_url())
    pdf_bytes = render_invoice_pdf_bytes(html)
    if invoice.pdf_file:
        invoice.pdf_file.delete(save=False)
    invoice.pdf_file.save(f"{invoice.invoice_number}.pdf", ContentFile(pdf_bytes), save=False)
    invoice.pdf_renderer = CHROMIUM_RENDERER
    invoice.save(update_fields=["pdf_file", "pdf_renderer"])
    return invoice


def invoice_base_url():
    return getattr(settings, "INVOICE_PUBLIC_BASE_URL", "") or "http://127.0.0.1:8000"


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
