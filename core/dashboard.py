"""کال‌بک داشبورد پنل — داده‌های واقعی را به قالب admin/index.html می‌دهد."""
from __future__ import annotations

from django.urls import reverse

from core import analytics
from core.charts import area_chart, donut, funnel, hbars, sparkline
from core.models import AuditLog, Notification

KPI_ICONS = {
    "sales": "trending_up",
    "rfq": "forum",
    "approval": "approval",
    "stock": "inventory_2",
    "credit": "account_balance_wallet",
}


def can_view_sales(user) -> bool:
    """آیا کاربر مجاز است اعداد فروش/مالی را ببیند؟"""
    return bool(
        user.is_superuser
        or user.has_perm("orders.view_order")
        or user.has_perm("finance.view_invoice")
    )


def dashboard_callback(request, context):
    """Unfold این تابع را با (request, context) صدا می‌زند.

    اگر کاربر مجوز دیدن سفارش‌ها/فاکتورها را نداشته باشد (مثلاً نقش «محتوا»)،
    نه اعداد فروش برایش محاسبه می‌شود و نه در قالب نمایش داده می‌شود؛ فقط
    کارت راهنما می‌بیند. این هم جلوی افشای اعداد مالی را می‌گیرد و هم چند
    کوئری سنگین را برای این نقش‌ها حذف می‌کند.
    """
    if not can_view_sales(request.user):
        return {**context, "can_view_sales": False}

    today = None
    kpi = analytics.kpis(today)
    series = analytics.sales_series(30)
    sales_chart = area_chart(series["values"], series["labels"], value_suffix="م.ت")

    status_rows = analytics.status_breakdown()
    status_donut = donut(status_rows, center_title=f"{sum(r['value'] for r in status_rows)}",
                         center_sub="سفارش ماه")

    sparks = analytics.sparklines(14)

    cart = {
        **context,
        "can_view_sales": True,
        "kpi": kpi,
        "sales_chart": sales_chart,
        "sales_spark": sparkline(series["values"][-14:]),
        "rfq_spark": sparkline(sparks["rfq"]),
        "orders_spark": sparkline(sparks["orders"]),
        "invoiced_spark": sparkline(sparks["invoiced"]),
        "status_donut": status_donut,
        "funnel_steps": funnel(analytics.funnel_counts(30)),
        "top_products": hbars(analytics.top_products(6)),
        "stock_alerts": analytics.stock_alerts(6),
        "rfq_board": analytics.rfq_board(6),
        "pending_approvals": analytics.pending_approval_list(5),
        "due_cheques": analytics.due_cheques(5),
        "recent_orders": analytics.recent_orders(6),
        "notifications": Notification.objects.filter(is_read=False).order_by("-created_at")[:6],
        "recent_audit": AuditLog.objects.select_related("actor")[:6],
        "monthly_sales": analytics.monthly_sales(6),
        "links": {
            "reports": reverse("panel-reports"),
            "quick_order": reverse("panel-quick-order"),
            "rfq": reverse("admin:quotes_quote_changelist"),
            "orders": reverse("admin:orders_order_changelist"),
            "approvals": reverse("admin:orders_approval_changelist") + "?status=pending",
            "stock": reverse("admin:inventory_stockitem_changelist"),
            "invoices": reverse("admin:finance_invoice_changelist"),
            "cheques": reverse("admin:finance_cheque_changelist"),
            "audit": reverse("admin:core_auditlog_changelist"),
            "alerts": reverse("panel-alerts"),
            "products": reverse("admin:catalog_product_changelist"),
            "companies": reverse("admin:customers_company_changelist"),
        },
    }
    return cart
