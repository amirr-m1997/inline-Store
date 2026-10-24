from django.contrib import admin
from django.core.exceptions import PermissionDenied
from datetime import timedelta

from django.db.models import Count, Exists, F, OuterRef, Q, Sum
from django.db.models.functions import TruncDate
from django.template.response import TemplateResponse
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductDocument, ProductImage, ProductQuestion, ProductReview
from apps.common.models import AuditEvent
from apps.inventory.models import Inventory, ReplenishmentRule
from apps.orders.models import Order, OrderItem
from apps.pricing.models import CustomerPriceList, ProductPrice
from apps.rfq.models import RequestForQuotation, SalesQuotation
from .management_reports import build_management_report, build_xlsx_response


def advanced_admin_index(request, extra_context=None):
    """داشبورد عملیاتی که مستقیماً از دیتابیس اصلی فروشگاه می‌خواند."""
    today = timezone.localdate()
    start = today - timedelta(days=29)
    daily_rows = (
        Order.objects.filter(created_at__date__gte=start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("final_amount"), count=Count("id"))
    )
    daily = {row["day"]: row for row in daily_rows}
    sales_series = []
    for offset in range(30):
        day = start + timedelta(days=offset)
        row = daily.get(day, {})
        sales_series.append({"label": day.strftime("%d/%m"), "total": int(row.get("total") or 0), "count": row.get("count", 0)})
    peak_sales = max((point["total"] for point in sales_series), default=0) or 1
    for point in sales_series:
        point["height"] = max(3, round(point["total"] * 100 / peak_sales)) if point["total"] else 3

    statuses = list(Order.objects.values("status").annotate(count=Count("id")))
    total_orders = sum(row["count"] for row in statuses)
    colors = {"pending_payment": "#f59e0b", "processing": "#0891b2", "confirmed": "#6366f1", "preparing": "#8b5cf6", "shipped": "#0ea5e9", "delivered": "#16a34a", "cancelled": "#dc2626", "returned": "#be123c"}
    status_slices, start_angle = [], 0
    for row in statuses:
        pct = round(row["count"] * 100 / total_orders) if total_orders else 0
        status_slices.append({"label": dict(Order.Status.choices).get(row["status"], row["status"]), "count": row["count"], "pct": pct, "color": colors.get(row["status"], "#64748b"), "start": start_angle, "end": start_angle + pct})
        start_angle += pct
    donut_gradient = ", ".join(f"{item['color']} {item['start']}% {item['end']}%" for item in status_slices) or "#dbe5ea 0 100%"

    top_products = list(
        Product.objects.filter(is_active=True)
        .annotate(sold_count=Sum("order_items__quantity"))
        .order_by("-sold_count", "name")[:6]
    )
    top_product_peak = max((item.sold_count or 0 for item in top_products), default=0) or 1
    now = timezone.now()
    active_products = Product.objects.filter(is_active=True)
    current_price = ProductPrice.objects.filter(
        product_id=OuterRef("pk"),
        effective_from__lte=now,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=now))
    product_image = ProductImage.objects.filter(product_id=OuterRef("pk"))
    product_document = ProductDocument.objects.filter(
        product_id=OuterRef("pk"), is_active=True, is_published=True,
    )
    catalog_health = {
        "without_price": active_products.annotate(has_current_price=Exists(current_price)).filter(has_current_price=False).count(),
        "without_image": active_products.annotate(has_image=Exists(product_image)).filter(has_image=False).count(),
        "without_document": active_products.annotate(has_document=Exists(product_document)).filter(has_document=False).count(),
        "without_specs": active_products.filter(Q(technical_specs={}) | Q(technical_specs__isnull=True)).count(),
        "active_contract_lists": CustomerPriceList.objects.filter(
            is_active=True, valid_from__lte=now,
        ).filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now)).count(),
    }
    replenishment_alerts = list(
        ReplenishmentRule.objects.filter(is_active=True)
        .select_related("product", "product__inventory")
        .filter(
            Q(product__inventory__isnull=True)
            | Q(product__inventory__on_hand_quantity__lte=F("product__inventory__reserved_quantity") + F("minimum_quantity"))
        )
        .order_by("lead_time_days", "product__name")[:8]
    )
    open_rfq_statuses = [
        RequestForQuotation.Status.SUBMITTED,
        RequestForQuotation.Status.UNDER_REVIEW,
    ]
    context = {
        **admin.site.each_context(request),
        "title": "داشبورد عملیاتی",
        "kpis": {
            "products": Product.objects.filter(is_active=True).count(),
            "categories": Category.objects.filter(is_active=True).count(),
            "orders_today": Order.objects.filter(created_at__date=today).count(),
            "open_rfq": RequestForQuotation.objects.exclude(status__in=["closed", "cancelled"]).count(),
            "inventory_items": Inventory.objects.count(),
        },
        "recent_orders": Order.objects.select_related("customer").order_by("-created_at")[:8],
        "recent_events": AuditEvent.objects.select_related("actor").order_by("-created_at")[:10],
        "sales_series": sales_series,
        "sales_total_30": sum(point["total"] for point in sales_series),
        "status_slices": status_slices,
        "donut_gradient": donut_gradient,
        "top_products": [{"name": item.name, "code": item.code, "value": item.sold_count or 0, "pct": max(3, round((item.sold_count or 0) * 100 / top_product_peak)) if item.sold_count else 3} for item in top_products],
        "low_stock": Inventory.objects.select_related("product").filter(
            on_hand_quantity__lte=F("reserved_quantity")
        ).order_by("on_hand_quantity")[:8],
        "top_categories": Category.objects.filter(is_active=True).annotate(
            product_count=Count("products")
        ).order_by("-product_count", "name_fa")[:8],
        "catalog_health": catalog_health,
        "pending_reviews": ProductReview.objects.filter(is_published=False).count(),
        "pending_questions": ProductQuestion.objects.filter(is_published=False, answer="").count(),
        "rfq_queue": RequestForQuotation.objects.filter(status__in=open_rfq_statuses).order_by("created_at")[:6],
        "draft_quotations": SalesQuotation.objects.filter(status=SalesQuotation.Status.DRAFT).count(),
        "replenishment_alerts": replenishment_alerts,
        "replenishment_alert_count": len(replenishment_alerts),
        "can_view_management_reports": request.user.has_perm("accounts.view_management_reports"),
    }
    if extra_context:
        context.update(extra_context)
    return TemplateResponse(request, "admin/advanced_index.html", context)


def management_reports_view(request):
    if not request.user.has_perm("accounts.view_management_reports"):
        raise PermissionDenied("دسترسی به گزارش‌های مدیریتی ندارید.")
    report = build_management_report(request.GET)
    context = {
        **admin.site.each_context(request),
        "title": "گزارش‌های مدیریتی",
        "report": report,
        "stale_day_options": (30, 60, 90, 180, 365),
        "report_tables": (("فروش بر اساس برند", report["brands"]), ("فروش بر اساس دسته", report["categories"]), ("فروش بر اساس مشتری", report["customers"])),
    }
    return TemplateResponse(request, "admin/dashboard/management_reports.html", context)


def management_report_export(request):
    if not request.user.has_perm("accounts.view_management_reports"):
        raise PermissionDenied("دسترسی به خروجی گزارش‌های مدیریتی ندارید.")
    return build_xlsx_response(build_management_report(request.GET))
