"""ادمین انبار: موجودی، رسید/حواله و درخواست خرید."""
from __future__ import annotations

from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)

from core.admin_utils import COLORS, PanelModelAdmin, badge, html_table, money_compact, progress_bar
from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter
from core.utils import jalali_dt, num

from .models import PurchaseRequest, StockItem, StockMove, Warehouse
from core.palette import INFO


class StockMoveInline(TabularInline):
    model = StockMove
    extra = 0
    can_delete = False
    fields = ("kind", "qty", "reference", "counterparty", "note", "created_by", "created_at")
    readonly_fields = ("kind", "qty", "reference", "counterparty", "note", "created_by", "created_at")
    verbose_name_plural = "آخرین تراکنش‌های انبار"
    tab = True
    per_page = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Warehouse)
class WarehouseAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "code", "kind", "keeper", "item_count", "stock_value_col", "is_active")
    list_filter = (("kind", ChoicesDropdownFilter), "is_active")
    search_fields = ("name", "code", "address")
    autocomplete_fields = ("keeper",)
    inlines = [StockMoveInline]

    @admin.display(description="تعداد قلم")
    def item_count(self, obj):
        return badge(f"{num(obj.stock_items.count())} قلم", key="primary")

    @admin.display(description="ارزش موجودی")
    def stock_value_col(self, obj):
        return money_compact(obj.stock_value)


@admin.register(StockItem)
class StockItemAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("product", "warehouse", "on_hand_col", "reserved_col", "free_col",
                    "incoming_col", "reorder_col", "status_badge", "value_col")
    list_display_links = ("product",)
    list_filter = (("warehouse", RelatedDropdownFilter),
                   ("product__category", RelatedDropdownFilter),
                   "product__availability", "product__is_active")
    search_fields = ("product__code", "product__name", "bin_location")
    autocomplete_fields = ("product", "warehouse")
    list_editable = ()
    actions = ["action_create_purchase_requests", "action_mark_stocktake"]
    readonly_fields = ("free_qty_display", "status_display", "value_display", "recent_moves",
                       "updated_at")
    fieldsets = (
        ("کالا و انبار", {"fields": ("product", "warehouse", "bin_location")}),
        ("مقادیر", {"fields": (("on_hand", "reserved", "incoming"),
                               ("min_level", "reorder_point"))}),
        ("محاسباتی", {"fields": ("free_qty_display", "status_display", "value_display")}),
        ("تاریخچه تراکنش‌ها", {"fields": ("recent_moves",)}),
        ("انبارگردانی", {"fields": ("last_stocktake", "updated_at"), "classes": ("collapse",)}),
    )

    # -------------------------------------------------- ستون‌ها
    @admin.display(description="موجودی", ordering="on_hand")
    def on_hand_col(self, obj):
        return format_html('<b style="font-variant-numeric:tabular-nums">{}</b>', num(obj.on_hand, 0))

    @admin.display(description="رزرو", ordering="reserved")
    def reserved_col(self, obj):
        return num(obj.reserved, 0)

    @admin.display(description="آزاد (ATP)")
    def free_col(self, obj):
        free = obj.free_qty
        color = COLORS["danger"] if free <= 0 else (COLORS["warn"] if free <= float(obj.reorder_point) else COLORS["ok"])
        return format_html('<b style="color:{};font-variant-numeric:tabular-nums">{}</b>', color, num(free, 0))

    @admin.display(description="در راه")
    def incoming_col(self, obj):
        value = float(obj.incoming)
        return badge(num(value, 0), key="info") if value else "—"

    @admin.display(description="نقطه سفارش", ordering="reorder_point")
    def reorder_col(self, obj):
        return num(obj.reorder_point, 0)

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        _, label, color = obj.status
        return badge(label, color=color)

    @admin.display(description="ارزش")
    def value_col(self, obj):
        return money_compact(obj.stock_value)

    # -------------------------------------------------- فیلدهای readonly
    @admin.display(description="موجودی آزاد قابل تعهد (ATP)")
    def free_qty_display(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            "<b>{}</b> {} — از {} {} موجودی و {} رزرو",
            num(obj.free_qty, 0), obj.product.get_uom_display(),
            num(obj.on_hand, 0), obj.product.get_uom_display(), num(obj.reserved, 0),
        )

    @admin.display(description="وضعیت و کمبود")
    def status_display(self, obj):
        if not obj.pk:
            return "—"
        _, label, color = obj.status
        shortage = obj.shortage_to_reorder
        html = badge(label, color=color)
        if shortage:
            html = format_html(
                "{} <span style='font-size:11.5px;color:var(--panel-warn)'>— کمبود تا نقطه سفارش: {} {}</span>",
                html, num(shortage, 0), obj.product.get_uom_display(),
            )
        return html

    @admin.display(description="ارزش ریالی موجودی")
    def value_display(self, obj):
        if not obj.pk:
            return "—"
        return money_compact(obj.stock_value)

    @admin.display(description="آخرین رسید و حواله‌های این کالا")
    def recent_moves(self, obj):
        if not obj.pk:
            return "—"
        rows = [
            [move.created_at.strftime("%Y-%m-%d %H:%M"), move.get_kind_display(),
             f"{move.qty}", move.reference or "—", move.created_by.username if move.created_by else "—"]
            for move in obj.product.stock_moves.select_related("created_by")[:12]
        ]
        return html_table(["زمان", "نوع", "مقدار", "مستند", "کاربر"], rows)

    # -------------------------------------------------- اکشن‌ها
    @admin.action(description="ایجاد درخواست خرید برای اقلام کم‌موجود")
    def action_create_purchase_requests(self, request, queryset):
        from .services import create_purchase_requests_for_low_stock

        created = create_purchase_requests_for_low_stock(user=request.user)
        self.message_user(request, f"{num(len(created))} درخواست خرید پیش‌نویس ساخته شد.",
                          messages.SUCCESS if created else messages.INFO)

    @admin.action(description="ثبت تاریخ انبارگردانی امروز")
    def action_mark_stocktake(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(last_stocktake=timezone.localdate())
        self.message_user(request, f"{num(updated)} رکورد انبارگردانی به‌روزرسانی شد.", messages.SUCCESS)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "warehouse")


@admin.register(StockMove)
class StockMoveAdmin(PanelModelAdmin, ModelAdmin):
    """رسید و حواله — تغییر موجودی فقط از طریق سرویس انبار انجام می‌شود."""
    list_select_related = ("product", "warehouse", "created_by")

    list_display = ("created_at_col", "kind_badge", "product", "warehouse", "qty_col",
                    "unit_cost_col", "reference", "counterparty", "order_link", "created_by")
    list_filter = (("kind", ChoicesDropdownFilter), ("warehouse", RelatedDropdownFilter),
                   ("occurred_on", RangeDateFilter))
    search_fields = ("product__code", "product__name", "reference", "counterparty", "note")
    autocomplete_fields = ("product", "warehouse", "order")
    list_filter = (("kind", ChoicesDropdownFilter), ("warehouse", RelatedDropdownFilter),
                   ("occurred_on", RangeDateFilter))
    fieldsets = (
        ("تراکنش", {"fields": ("kind", "product", "warehouse", "qty", "unit_cost")}),
        ("مستندات", {"fields": ("reference", "counterparty", "order", "occurred_on", "note")}),
    )

    @admin.display(description="زمان", ordering="created_at")
    def created_at_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        return badge(obj.get_kind_display(), color=obj.kind_color)

    @admin.display(description="مقدار", ordering="qty")
    def qty_col(self, obj):
        sign = "−" if obj.kind in ("issue", "reserve") else "+"
        color = COLORS["danger"] if sign == "−" else COLORS["ok"]
        return format_html('<b style="color:{};font-variant-numeric:tabular-nums">{}{}</b>',
                           color, sign, num(obj.qty, 0))

    @admin.display(description="بهای واحد")
    def unit_cost_col(self, obj):
        return money_compact(obj.unit_cost)

    @admin.display(description="سفارش")
    def order_link(self, obj):
        if not obj.order_id:
            return "—"
        from django.urls import reverse

        url = reverse("admin:orders_order_change", args=[obj.order_id])
        return format_html('<a href="{}">{}</a>', url, obj.order.number)

    def save_model(self, request, obj, form, change):
        """ثبت تراکنش از طریق سرویس (به‌روزرسانی خودکار موجودی)."""
        if change:
            return super().save_model(request, obj, form, change)
        from .services import apply_move

        move = apply_move(
            product=obj.product, warehouse=obj.warehouse, kind=obj.kind, qty=obj.qty,
            unit_cost=obj.unit_cost, reference=obj.reference, order=obj.order,
            note=obj.note, user=request.user, counterparty=obj.counterparty,
        )
        obj.pk = move.pk
        obj.created_by = request.user
        messages.success(request, f"تراکنش ثبت و موجودی به‌روزرسانی شد ({obj.get_kind_display()}).")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("product", "warehouse", "requested_by")
    list_display = ("id", "product", "warehouse", "qty_col", "status_badge", "needed_by_col",
                    "supplier", "estimated_cost_col", "requested_by", "created_at_col")
    list_filter = (("status", ChoicesDropdownFilter), ("warehouse", RelatedDropdownFilter),
                   ("product__category", RelatedDropdownFilter))
    search_fields = ("product__code", "product__name", "supplier", "note")
    autocomplete_fields = ("product", "warehouse", "requested_by")
    actions = ["action_approve", "action_mark_ordered", "action_mark_received"]
    readonly_fields = ("created_at",)
    fieldsets = (
        ("درخواست", {"fields": ("product", "warehouse", "qty", "needed_by", "status")}),
        ("تأمین", {"fields": ("supplier", "estimated_cost", "note")}),
        ("ردیابی", {"fields": ("requested_by", "created_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="مقدار", ordering="qty")
    def qty_col(self, obj):
        return format_html("<b>{}</b> {}", num(obj.qty, 0), obj.product.get_uom_display())

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="مورد نیاز تا", ordering="needed_by")
    def needed_by_col(self, obj):
        from core.utils import jalali

        return jalali(obj.needed_by) if obj.needed_by else "—"

    @admin.display(description="برآورد هزینه")
    def estimated_cost_col(self, obj):
        return money_compact(obj.estimated_cost)

    @admin.display(description="تاریخ", ordering="created_at")
    def created_at_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.action(description="تأیید درخواست خرید")
    def action_approve(self, request, queryset):
        queryset.update(status="approved")

    @admin.action(description="ثبت صدور سفارش خرید")
    def action_mark_ordered(self, request, queryset):
        queryset.update(status="ordered")

    @admin.action(description="ثبت دریافت و ورود به انبار")
    def action_mark_received(self, request, queryset):
        from .services import apply_move

        count = 0
        for pr in queryset.select_related("product", "warehouse"):
            apply_move(product=pr.product, warehouse=pr.warehouse, kind="receipt", qty=pr.qty,
                       unit_cost=pr.estimated_cost and int(pr.estimated_cost / float(pr.qty or 1)) or 0,
                       reference=f"PR-{pr.pk}", note=f"دریافت درخواست خرید {pr.pk}",
                       user=request.user, counterparty=pr.supplier)
            pr.status = "received"
            pr.save(update_fields=["status"])
            count += 1
        self.message_user(request, f"{num(count)} درخواست دریافت و به موجودی اضافه شد.", messages.SUCCESS)
