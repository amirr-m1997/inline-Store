"""سرویس مشتریان: اعتبار، مطالبات و سنّی‌بندی."""
from __future__ import annotations

from django.utils import timezone

from finance.models import Cheque, Invoice


def credit_snapshot(company) -> dict:
    """تصویر کامل وضعیت اعتبار مشتری برای نمایش در پنل."""
    open_invoices = list(
        Invoice.objects.filter(company=company).exclude(status__in=["paid", "cancelled", "draft"])
        .order_by("due_date")
    )
    receivable = sum(inv.balance for inv in open_invoices)
    cheques = list(Cheque.objects.filter(company=company, direction="received",
                                         status__in=["in_hand", "deposited"]))
    cheque_total = sum(ch.amount for ch in cheques)
    overdue = [inv for inv in open_invoices if inv.due_date and inv.due_date < timezone.localdate()]
    return {
        "limit": company.credit_limit,
        "receivable": receivable,
        "cheques": cheque_total,
        "used": receivable + cheque_total,
        "available": max(company.credit_limit - (receivable + cheque_total), 0),
        "usage_pct": company.credit_usage_pct,
        "open_invoices": len(open_invoices),
        "overdue_invoices": len(overdue),
        "oldest_due": open_invoices[0].due_date if open_invoices else None,
        "cheques_near_due": [ch for ch in cheques if 0 <= ch.days_to_due <= 7],
    }


def can_place_order(company, amount: int) -> dict:
    """آیا مشتری می‌تواند سفارش به این مبلغ ثبت کند؟"""
    snapshot = credit_snapshot(company)
    if company.is_blacklisted:
        return {"allowed": False, "reason": "مشتری در لیست سیاه است.", "snapshot": snapshot}
    if company.kyc_status != "approved":
        return {"allowed": False, "reason": "احراز هویت (KYC) مشتری تأیید نشده است.", "snapshot": snapshot}
    if not snapshot["limit"]:
        return {"allowed": True, "reason": "بدون سقف اعتبار (نقدی/پیش‌پرداخت)", "snapshot": snapshot}
    if amount > snapshot["available"]:
        return {
            "allowed": False,
            "reason": f"مبلغ سفارش از اعتبار آزاد ({snapshot['available']:,} تومان) بیشتر است؛ نیاز به تأیید مالی.",
            "snapshot": snapshot,
        }
    return {"allowed": True, "reason": "در محدوده اعتبار", "snapshot": snapshot}


def aging_report(company=None) -> dict[str, int]:
    """سنّی‌بندی مطالبات: ۰-۳۰ / ۳۱-۶۰ / ۶۱-۹۰ / +۹۰ روز."""
    today = timezone.localdate()
    buckets = {"0_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}
    qs = Invoice.objects.exclude(status__in=["paid", "cancelled", "draft"])
    if company is not None:
        qs = qs.filter(company=company)
    for invoice in qs.select_related("company"):
        reference = invoice.due_date or invoice.issued_at
        days = (today - reference).days
        if days <= 30:
            buckets["0_30"] += invoice.balance
        elif days <= 60:
            buckets["31_60"] += invoice.balance
        elif days <= 90:
            buckets["61_90"] += invoice.balance
        else:
            buckets["90_plus"] += invoice.balance
    buckets["total"] = sum(v for k, v in buckets.items() if k != "total")
    return buckets
