import logging
from celery import shared_task

logger = logging.getLogger("orders.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_send_invoice_email(self, order_id, recipient=None):
    """Asynchronously generate invoice and send email notification to customer."""
    from apps.orders.models import Order
    from apps.orders.services import create_invoice, email_invoice

    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return f"Order {order_id} not found"
    try:
        invoice = create_invoice(order)
        target = recipient or order.customer_email
        if target:
            email_invoice(invoice, target)
            return f"Sent invoice for order {order_id} to {target}"
        return f"No email for order {order_id}"
    except Exception as exc:
        logger.error("Failed to async email invoice for order %s: %s", order_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_generate_invoice_pdf(self, order_id, base_url=""):
    """Asynchronously generate PDF invoice and store on invoice instance."""
    from apps.orders.models import Order
    from apps.orders.services import create_invoice, ensure_invoice_pdf

    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return f"Order {order_id} not found"
    try:
        invoice = create_invoice(order)
        ensure_invoice_pdf(invoice, base_url=base_url)
        return f"Generated PDF for order {order_id}"
    except Exception as exc:
        logger.error("Failed to async generate invoice PDF for order %s: %s", order_id, exc)
        raise self.retry(exc=exc)
