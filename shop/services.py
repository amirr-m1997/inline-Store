"""لایهٔ سرویس سایت مشتری (فروشگاه).

هدف: منطق «ثبت سفارش + صدور پیش‌فاکتور» و «وضعیت اعتبار» در یک نقطه بماند تا
نمای checkout فقط مسئول اعتبارسنجی فرم و پاسخ‌دهی HTTP باشد. این توابع بعداً
از طریق API موبایل/پنل نمایندگی یا آزمون‌های خودکار هم قابل استفاده‌اند.
"""
from __future__ import annotations

from orders.services import create_invoice, create_order


def credit_snapshot(company) -> dict | None:
    """وضعیت اعتبار مشتری برای نمایش در صفحهٔ ثبت سفارش (None اگر سقفی ثبت نشده)."""
    if company is None or not company.credit_limit:
        return None
    return {
        "used": company.credit_used,
        "limit": company.credit_limit,
        "available": company.credit_available,
        "pct": company.credit_usage_pct,
        "status": company.credit_status,
    }


def over_credit(credit: dict | None, amount: int) -> bool:
    """آیا مبلغ سفارش از اعتبار قابل استفادهٔ مشتری بیشتر است؟"""
    return bool(credit and amount > credit["available"])


def place_order(*, company, membership, user, rows, po_number: str = "", project_name: str = "",
                customer_note: str = "", shipping_address=None,
                shipping_method: str = "pickup", payment_method: str = "credit"):
    """ثبت سفارش از سایت + صدور پیش‌فاکتور؛ (order, invoice) برمی‌گرداند."""
    order = create_order(
        company=company,
        rows=rows,
        actor=user,
        po_number=po_number,
        project_name=project_name,
        customer_note=customer_note,
        contact=membership,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        payment_method=payment_method,
    )
    invoice = create_invoice(order, user=user, kind="proforma")
    return order, invoice
