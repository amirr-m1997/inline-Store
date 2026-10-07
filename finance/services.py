"""سرویس مالی: پرداخت، چک و ارسال به سامانه مؤدیان."""
from __future__ import annotations

import random
from datetime import timedelta

from django.utils import timezone

from core import audit
from core.models import AuditLog

from .models import Cheque, Invoice, Payment

VALIDATION_ERRORS = {
    "no_economic_code": "کد اقتصادی خریدار ثبت نشده است (الزام صورتحساب نوع اول).",
    "no_total": "مبلغ فاکتور صفر است.",
    "bad_lines": "شرح ردیف‌ها ناقص است.",
}


def validate_for_moadian(invoice: Invoice) -> list[str]:
    """اعتبارسنجی پیش از ارسال به سامانه مؤدیان."""
    errors = []
    if invoice.company.is_legal and not invoice.buyer_economic_code:
        errors.append(VALIDATION_ERRORS["no_economic_code"])
    if not invoice.total:
        errors.append(VALIDATION_ERRORS["no_total"])
    if not invoice.lines.exists():
        errors.append(VALIDATION_ERRORS["bad_lines"])
    return errors


def submit_to_moadian(invoice: Invoice, user=None) -> Invoice:
    """ارسال صورتحساب الکترونیکی (شبیه‌سازی واسط مؤدیان).

    در پیاده‌سازی واقعی این متد به API نرم‌افزار واسط مورد تأیید سازمان مالیاتی وصل می‌شود.
    """
    errors = validate_for_moadian(invoice)
    if errors:
        invoice.moadian_status = "failed"
        invoice.moadian_error = " | ".join(errors)
        invoice.save(update_fields=["moadian_status", "moadian_error"])
        return invoice
    invoice.moadian_status = "submitted"
    invoice.moadian_sent_at = timezone.now()
    invoice.status = "sent"
    invoice.moadian_tax_id = f"{random.randint(10**15, 10**16 - 1)}"
    invoice.moadian_error = ""
    invoice.save(update_fields=["moadian_status", "moadian_sent_at", "moadian_tax_id", "status",
                                "moadian_error"])
    audit.log(action=AuditLog.Action.STATUS, instance=invoice, actor=user,
              note=f"ارسال به سامانه مؤدیان — شناسه مالیاتی {invoice.moadian_tax_id}",
              after={"moadian_status": "submitted", "tax_id": invoice.moadian_tax_id})
    return invoice


def register_payment(*, company, amount: int, method: str = "transfer", invoice: Invoice | None = None,
                     order=None, reference: str = "", bank: str = "", user=None,
                     paid_at=None) -> Payment:
    payment = Payment.objects.create(
        company=company, invoice=invoice, order=order, method=method, amount=amount,
        reference=reference, bank=bank, created_by=user,
        paid_at=paid_at or timezone.localdate(),
    )
    if invoice is not None:
        payment.apply_to_invoice()
    if order is not None:
        audit.log(action=AuditLog.Action.STATUS, instance=order, actor=user,
                  note=f"ثبت پرداخت {amount:,} تومان ({method})", after={"payment": amount})
    return payment


def deposit_cheque(cheque: Cheque, user=None, when=None):
    cheque.status = "deposited"
    cheque.deposited_at = when or timezone.localdate()
    cheque.save(update_fields=["status", "deposited_at"])
    return cheque


def clear_cheque(cheque: Cheque, user=None, when=None):
    cheque.status = "cleared"
    cheque.cleared_at = when or timezone.localdate()
    cheque.save(update_fields=["status", "cleared_at"])
    if cheque.invoice_id:
        register_payment(company=cheque.company, amount=cheque.amount, method="cheque",
                         invoice=cheque.invoice, order=cheque.order,
                         reference=f"چک {cheque.number}", bank=cheque.bank, user=user,
                         paid_at=cheque.cleared_at)
    return cheque


def bounce_cheque(cheque: Cheque, reason: str, user=None):
    cheque.status = "bounced"
    cheque.bounce_reason = reason
    cheque.save(update_fields=["status", "bounce_reason"])
    audit.log(action=AuditLog.Action.STATUS, instance=cheque, actor=user,
              note=f"چک برگشتی: {reason}", after={"status": "bounced"})
    return cheque


def due_cheques(days: int = 7):
    """چک‌های نزدیک سررسید یا معوق."""
    today = timezone.localdate()
    return Cheque.objects.filter(
        status__in=["in_hand", "deposited"],
        due_date__lte=today + timedelta(days=days),
    ).select_related("company").order_by("due_date")


def unpaid_invoices():
    return Invoice.objects.exclude(status__in=["paid", "cancelled", "draft"]).select_related("company")
