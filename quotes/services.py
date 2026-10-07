"""سرویس استعلام: SLA، ارجاع، تبدیل به سفارش."""
from __future__ import annotations

from django.utils import timezone

from core import audit
from core.models import AuditLog

from .models import Quote, QuoteMessage


def assign(quote: Quote, user, actor=None) -> Quote:
    quote.assigned_to = user
    if quote.status == "new":
        quote.status = "tech_review"
    quote.save(update_fields=["assigned_to", "status"])
    QuoteMessage.objects.create(
        quote=quote, author=actor or user, kind="status", is_internal=True,
        body=f"ارجاع به {user.get_full_name() or user.username}",
    )
    return quote


def add_message(quote: Quote, body: str, author=None, is_internal: bool = True,
                kind: str = "message", author_name: str = "") -> QuoteMessage:
    message = QuoteMessage.objects.create(
        quote=quote, author=author, body=body, is_internal=is_internal, kind=kind,
        author_name=author_name,
    )
    if not quote.first_response_at and not is_internal:
        quote.first_response_at = timezone.now()
        quote.status = "sent" if quote.status in ("new", "tech_review", "pricing") else quote.status
        quote.save(update_fields=["first_response_at", "status"])
    return message


def recalc_prices(quote: Quote, save: bool = True) -> Quote:
    for line in quote.lines.select_related("product"):
        line.apply_price(company=quote.company, save=True)
    if save:
        quote.version += 1
        quote.save(update_fields=["version"])
    return quote


def send_offer(quote: Quote, user=None, note: str = "") -> Quote:
    quote.status = "sent"
    if not quote.first_response_at:
        quote.first_response_at = timezone.now()
    quote.save(update_fields=["status", "first_response_at"])
    add_message(
        quote,
        note or f"پیش‌فاکتور نسخه {quote.version} برای مشتری ارسال شد.",
        author=user, is_internal=False, kind="offer",
    )
    return quote


def convert_to_order(quote: Quote, user=None, po_number: str = "", payment_method: str = "cash"):
    """تبدیل استعلام به سفارش با کپی ردیف‌ها و قواعد تأیید."""
    from orders.models import Order, OrderLine
    from orders.services import evaluate_approvals

    order = Order.objects.create(
        company=quote.company, contact=quote.contact, po_number=po_number,
        project_name=quote.project_name, payment_method=payment_method,
        payment_terms=quote.payment_terms, discount_pct=quote.discount_pct,
        sales_rep=quote.assigned_to, created_by=user,
        customer_note=quote.customer_note, internal_note=f"تبدیل‌شده از {quote.number}",
        placed_by_rep_for_company=True,
    )
    for line in quote.lines.select_related("product"):
        OrderLine.objects.create(
            order=order, product=line.product, qty=line.qty, unit_price=line.offered_price,
            list_price=line.list_price, discount_pct=line.discount_pct,
            lead_time_days=line.lead_time_days, spec_note=line.availability_note,
        )
    quote.status = "converted"
    quote.order = order
    quote.save(update_fields=["status", "order"])
    evaluate_approvals(order, actor=user)
    audit.log(action=AuditLog.Action.STATUS, instance=quote, actor=user,
              note=f"تبدیل استعلام به سفارش {order.number}",
              before={"status": "sent"}, after={"status": "converted"})
    return order


def overdue_quotes():
    """استعلام‌های باز که از SLA عبور کرده‌اند."""
    return Quote.objects.filter(
        status__in=["new", "tech_review", "pricing", "sent", "negotiation"],
        sla_due_at__lt=timezone.now(),
    ).order_by("sla_due_at")
