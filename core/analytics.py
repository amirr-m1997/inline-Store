"""تحلیل داده‌ها برای داشبورد و گزارش‌ها (بدون کوئری سنگین در قالب)."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import (
    BigIntegerField,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.db.models.functions import TruncDate
from django.utils import timezone

from finance.models import Cheque, Invoice, Payment
from inventory.models import StockItem
from orders.models import Approval, Order, OrderLine
from quotes.models import Quote

MONEY = BigIntegerField()

NET_LINE = ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=20, decimal_places=2))

OPEN_ORDER_STATUSES = ["approved", "reserved", "ready", "shipped", "delivered", "closed"]
ACTIVE_RFQ_STATUSES = ["new", "tech_review", "pricing", "sent", "negotiation"]


def _orders_with_totals():
    """کوئری پایه سفارش‌ها با جمع ردیف‌ها و مبلغ ناخالص."""
    return (
        Order.objects.exclude(status__in=["draft", "cancelled"])
        .annotate(
            lines_total=Sum(ExpressionWrapper(F("lines__qty") * F("lines__unit_price"),
                                              output_field=MONEY)),
            cost_total=Sum(ExpressionWrapper(F("lines__qty") * F("lines__unit_cost"),
                                             output_field=MONEY)),
        )
    )


def order_net(order) -> int:
    """مبلغ ناخالص سفارش (پس از تخفیف، بدون ارزش افزوده)."""
    lines_total = order.lines_total or 0
    return int(lines_total) - int(int(lines_total) * float(order.discount_pct or 0) / 100)


def kpis(today=None) -> dict:
    """کارت‌های کلیدی داشبورد."""
    today = today or timezone.localdate()
    month_start = today.replace(day=1)

    paid_today = Payment.objects.filter(paid_at=today).aggregate(s=Sum("amount"))["s"] or 0
    sales_today_orders = _orders_with_totals().filter(ordered_at__date=today)
    sales_today = sum(order_net(o) for o in sales_today_orders)
    month_orders = _orders_with_totals().filter(ordered_at__date__gte=month_start)
    month_sales = sum(order_net(o) for o in month_orders)

    open_rfqs = Quote.objects.filter(status__in=ACTIVE_RFQ_STATUSES)
    overdue_rfqs = [q for q in open_rfqs if q.is_sla_overdue]
    pending_approvals = Approval.objects.filter(status="pending")
    pending_orders = Order.objects.filter(status="pending_approval")

    low_stock = [item for item in StockItem.objects.select_related("product", "warehouse")
                 if item.status[0] in ("critical", "low", "out", "error")]

    receivable = sum(inv.balance for inv in Invoice.objects.exclude(
        status__in=["paid", "cancelled", "draft"]))
    cheques_soon = Cheque.objects.filter(status__in=["in_hand", "deposited"],
                                         due_date__lte=today + timedelta(days=7),
                                         due_date__gte=today - timedelta(days=30)).count()

    yesterday_orders = _orders_with_totals().filter(ordered_at__date=today - timedelta(days=1))
    sales_yesterday = sum(order_net(o) for o in yesterday_orders)
    delta_pct = round((sales_today - sales_yesterday) * 100 / sales_yesterday) if sales_yesterday else 0

    return {
        "sales_today": sales_today,
        "sales_today_delta": delta_pct,
        "sales_month": month_sales,
        "month_orders": month_orders.count(),
        "payments_today": int(paid_today),
        "open_rfqs": open_rfqs.count(),
        "overdue_rfqs": len(overdue_rfqs),
        "pending_approvals": pending_approvals.count(),
        "pending_orders": pending_orders.count(),
        "low_stock_count": len(low_stock),
        "critical_stock_count": len([i for i in low_stock if i.status[0] in ("critical", "out", "error")]),
        "receivable": receivable,
        "cheques_soon": cheques_soon,
    }


def sales_series(days: int = 30) -> dict:
    """سری روزانه‌ی فروش برای نمودار."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    rows = (
        _orders_with_totals()
        .filter(ordered_at__date__gte=start)
        .values("ordered_at__date")
        .order_by("ordered_at__date")
        .annotate(count=Count("id"))
    )
    by_date = {}
    for order in _orders_with_totals().filter(ordered_at__date__gte=start).select_related():
        key = timezone.localtime(order.ordered_at).date()
        by_date[key] = by_date.get(key, 0) + order_net(order)
    values, labels = [], []
    for offset in range(days):
        day = start + timedelta(days=offset)
        values.append(by_date.get(day, 0))
        labels = labels + [f"{day.day}"]
    import jdatetime

    first = jdatetime.date.fromgregorian(date=start).strftime("%m")
    return {"values": values, "labels": labels, "month_label": first, "start": start}


def status_breakdown() -> list[dict]:
    """تفکیک وضعیت سفارش‌ها برای دونات."""
    colors = {
        "draft": "#64748b", "pending_approval": "#b45309", "approved": "#0e7490",
        "reserved": "#0891b2", "ready": "#22a5c0", "shipped": "#1d4ed8",
        "delivered": "#12855f", "closed": "#64748b", "cancelled": "#c02626",
    }
    rows = Order.objects.values("status").annotate(count=Count("id")).order_by("-count")
    return [
        {"label": dict(Order._meta.get_field("status").choices)[row["status"]],
         "value": row["count"], "color": colors.get(row["status"], "#64748b")}
        for row in rows
    ]


def funnel_counts(days: int = 30) -> list[dict]:
    """قیف استعلام → سفارش."""
    since = timezone.now() - timedelta(days=days)
    quotes = Quote.objects.filter(created_at__gte=since)
    created = quotes.count()
    responded = quotes.exclude(first_response_at=None).count()
    offered = quotes.filter(status__in=["sent", "negotiation", "won", "converted"]).count()
    converted = quotes.filter(status="converted").count()
    return [
        {"label": "استعلام ثبت‌شده", "value": created, "color": "#155e75"},
        {"label": "پاسخ‌داده‌شده", "value": responded, "color": "#0e7490"},
        {"label": "پیش‌فاکتور صادرشده", "value": offered, "color": "#0891b2"},
        {"label": "تبدیل به سفارش", "value": converted, "color": "#22a5c0"},
    ]


def top_products(limit: int = 6, days: int = 30) -> list[dict]:
    since = timezone.now() - timedelta(days=days)
    rows = (
        OrderLine.objects.filter(order__ordered_at__gte=since)
        .exclude(order__status__in=["draft", "cancelled"])
        .values("product__code", "product__name")
        .annotate(amount=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=MONEY)),
                  qty=Sum("qty"))
        .order_by("-amount")[:limit]
    )
    return [
        {"label": row["product__name"], "code": row["product__code"],
         "value": int(row["amount"] or 0), "qty": float(row["qty"] or 0)}
        for row in rows
    ]


def sales_by(dimension: str = "province", start=None, end=None, company=None, status=None) -> dict:
    """گزارش فروش گروه‌بندی‌شده بر اساس بُعد انتخابی."""
    qs = _orders_with_totals()
    if start:
        qs = qs.filter(ordered_at__date__gte=start)
    if end:
        qs = qs.filter(ordered_at__date__lte=end)
    if company:
        qs = qs.filter(company=company)
    if status:
        qs = qs.filter(status=status)

    field_map = {
        "province": ("company__province", "استان"),
        "category": ("lines__product__category__name", "دسته کالا"),
        "brand": ("lines__product__brand__name", "برند"),
        "rep": ("sales_rep__username", "کارشناس فروش"),
        "company": ("company__name", "مشتری"),
        "product": ("lines__product__name", "محصول"),
        "payment": ("payment_method", "روش پرداخت"),
        "month": ("ordered_at__month", "ماه"),
    }
    field, title = field_map.get(dimension, field_map["province"])

    if dimension == "category":
        rows = (OrderLine.objects.filter(order__in=qs.values("id") if False else qs)
                .values("product__category__name")
                .annotate(amount=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=MONEY)),
                          qty=Sum("qty"), orders=Count("order", distinct=True))
                .order_by("-amount"))
        data = [
            {"label": r["product__category__name"] or "بدون دسته", "amount": int(r["amount"] or 0),
             "orders": r["orders"], "qty": float(r["qty"] or 0)}
            for r in rows
        ]
    elif dimension == "brand":
        rows = (OrderLine.objects.filter(order__in=qs)
                .values("product__brand__name")
                .annotate(amount=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=MONEY)),
                          qty=Sum("qty"), orders=Count("order", distinct=True))
                .order_by("-amount"))
        data = [
            {"label": r["product__brand__name"] or "بدون برند", "amount": int(r["amount"] or 0),
             "orders": r["orders"], "qty": float(r["qty"] or 0)}
            for r in rows
        ]
    elif dimension == "product":
        rows = (OrderLine.objects.filter(order__in=qs)
                .values("product__name", "product__code")
                .annotate(amount=Sum(ExpressionWrapper(F("qty") * F("unit_price"), output_field=MONEY)),
                          qty=Sum("qty"), orders=Count("order", distinct=True))
                .order_by("-amount")[:50])
        data = [
            {"label": f"{r['product__name']} ({r['product__code']})",
             "amount": int(r["amount"] or 0), "orders": r["orders"], "qty": float(r["qty"] or 0)}
            for r in rows
        ]
    else:
        rows = qs.values(field).annotate(orders=Count("id")).order_by()
        data = []
        for row in rows:
            label = row.get(field) or "نامشخص"
            if dimension == "rep" and label:
                from django.contrib.auth import get_user_model

                user = get_user_model().objects.filter(username=label).first()
                label = (user.get_full_name() or label) if user else label
            if dimension == "payment":
                label = dict(Order._meta.get_field("payment_method").choices).get(label, label)
            if dimension == "month":
                label = f"ماه {label}"
            subtotal = sum(order_net(o) for o in qs.filter(**{field: row.get(field)}))
            data.append({"label": str(label), "amount": subtotal, "orders": row["orders"], "qty": 0})
        data.sort(key=lambda r: -r["amount"])

    total = sum(row["amount"] for row in data) or 1
    for row in data:
        row["share_pct"] = round(row["amount"] * 100 / total, 1)
    return {"dimension": dimension, "title": title, "rows": data, "total": total}


def report_summary(start=None, end=None) -> dict:
    """خلاصه‌ی دوره برای گزارش‌ساز."""
    qs = _orders_with_totals()
    if start:
        qs = qs.filter(ordered_at__date__gte=start)
    if end:
        qs = qs.filter(ordered_at__date__lte=end)
    rows = list(qs)
    sales = sum(order_net(o) for o in rows)
    cost = sum(int(o.cost_total or 0) for o in rows)
    discount = sum(int(o.lines_total or 0) * float(o.discount_pct or 0) / 100 for o in rows)
    invoices = Invoice.objects.exclude(status__in=["cancelled"])
    if start:
        invoices = invoices.filter(issued_at__gte=start)
    if end:
        invoices = invoices.filter(issued_at__lte=end)
    return {
        "sales": sales,
        "orders": len(rows),
        "avg_basket": int(sales / len(rows)) if rows else 0,
        "cost": cost,
        "gross_profit": sales - cost,
        "margin_pct": round((sales - cost) * 100 / sales, 1) if sales else 0,
        "discount": int(discount),
        "discount_pct": round(discount * 100 / sales, 2) if sales else 0,
        "active_customers": len({o.company_id for o in rows}),
        "invoices": invoices.count(),
        "invoiced": sum(inv.total for inv in invoices),
        "collected": sum(inv.paid_amount for inv in invoices),
    }


def stock_alerts(limit: int = 8) -> list[StockItem]:
    items = [item for item in StockItem.objects.select_related("product", "warehouse")
             if item.status[0] in ("critical", "low", "out", "error")]
    items.sort(key=lambda i: (i.free_qty, -float(i.reorder_point)))
    return items[:limit]


def rfq_board(limit: int = 6) -> list[Quote]:
    return list(
        Quote.objects.filter(status__in=ACTIVE_RFQ_STATUSES)
        .select_related("company", "assigned_to")
        .order_by("sla_due_at")[:limit]
    )


def pending_approval_list(limit: int = 6):
    return list(Approval.objects.filter(status="pending").select_related("order__company").order_by("created_at")[:limit])


def due_cheques(limit: int = 6):
    return list(
        Cheque.objects.filter(status__in=["in_hand", "deposited"])
        .select_related("company")
        .order_by("due_date")[:limit]
    )


def recent_orders(limit: int = 6):
    return list(Order.objects.select_related("company", "sales_rep").order_by("-ordered_at")[:limit])


def searches_without_result(limit: int = 5) -> list[dict]:
    """جست‌وجوهای بی‌نتیجه — نمونه‌ی آماده برای اتصال به لاگ جست‌وجوی سایت."""
    return []


def monthly_sales(months: int = 6) -> dict:
    """فروش ماهانه برای گزارش مدیریتی (میلادی → برچسب شمسی)."""
    import jdatetime

    today = timezone.localdate()
    buckets: dict[str, int] = {}
    labels = []
    for offset in range(months - 1, -1, -1):
        month_index = today.month - offset
        year = today.year
        while month_index <= 0:
            month_index += 12
            year -= 1
        j = jdatetime.date.fromgregorian(date=today.replace(year=year, month=month_index, day=1))
        key = f"{year}-{month_index:02d}"
        buckets[key] = 0
        labels.append(j.strftime("%B %Y") if False else f"{j.month}/{str(j.year)[-2:]}")

    for order in _orders_with_totals():
        local = timezone.localtime(order.ordered_at)
        key = f"{local.year}-{local.month:02d}"
        if key in buckets:
            buckets[key] += order_net(order)
    return {"values": list(buckets.values()), "labels": labels}


# ------------------------------------------------------------------ اسپارک‌لاین‌های KPI
def sparklines(days: int = 14) -> dict:
    """سری‌های کوچک روزانه برای نمودار جرقه‌ای کارت‌های KPI.

    برای شاخص موجودی کم‌موجود (که وضعیت لحظه‌ای است و تاریخچه ندارد) عمداً
    سری ساخته نمی‌شود تا نمودار گمراه‌کننده نمایش داده نشود.
    """
    from datetime import timedelta

    from django.db.models import Count

    from finance.models import Invoice
    from quotes.models import Quote

    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    def _empty() -> list[int]:
        return [0] * days

    def _buckets(qs, date_lookup: str, extractor=lambda row: 1) -> list[int]:
        """شمارش/جمع رکوردها به تفکیک روز بر اساس یک lookup تاریخ."""
        out = _empty()
        for row in qs.values(date_lookup).annotate(n=Count("id")):
            day = row[date_lookup]
            if hasattr(day, "date"):
                day = timezone.localtime(day).date()
            idx = (day - start).days
            if 0 <= idx < days:
                out[idx] += int(extractor(row))
        return out

    # فروش: مبلغ خالص سفارش‌ها (هم‌سبک با sales_series تا اعداد یکسان باشد)
    sales = _empty()
    for order in _orders_with_totals().filter(ordered_at__date__gte=start):
        idx = (timezone.localtime(order.ordered_at).date() - start).days
        if 0 <= idx < days:
            sales[idx] += order_net(order)

    rfq = _buckets(Quote.objects.filter(created_at__date__gte=start), "created_at__date")
    orders = _buckets(Order.objects.filter(ordered_at__date__gte=start), "ordered_at__date")
    invoiced = _buckets(
        Invoice.objects.filter(issued_at__gte=start, kind="sale"),
        "issued_at",
    )
    return {"sales": sales, "rfq": rfq, "orders": orders, "invoiced": invoiced, "days": days}
