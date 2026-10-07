"""ادمین سفارش‌ها و گردش تأیید."""
from __future__ import annotations

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)
from unfold.decorators import action
from unfold.enums import ActionVariant

from core.admin_utils import COLORS, PanelModelAdmin, badge, html_table, money_compact, progress_bar
from core.utils import jalali, jalali_dt, num
from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter

from .models import Approval, ApprovalRule, Order, OrderEvent, OrderLine
from core.palette import ACCENT, DANGER


class OrderLineInline(TabularInline):
    model = OrderLine
    extra = 0
    autocomplete_fields = ("product", "warehouse")
    fields = ("product", "qty", "unit_price", "discount_pct", "qty_reserved", "qty_shipped",
              "warehouse", "lead_time_days", "spec_note")
    verbose_name_plural = "ردیف‌های سفارش"
    tab = True


class ApprovalInline(TabularInline):
    model = Approval
    extra = 0
    can_delete = False
    fields = ("step", "required_role", "status", "approver", "amount_snapshot", "comment", "acted_at")
    readonly_fields = ("step", "required_role", "status", "approver", "amount_snapshot", "comment",
                       "acted_at")
    verbose_name_plural = "گردش تأیید"
    tab = True

    def has_add_permission(self, request, obj=None):
        return False


class OrderEventInline(TabularInline):
    model = OrderEvent
    extra = 0
    can_delete = False
    fields = ("created_at", "kind", "title", "description", "actor")
    readonly_fields = ("created_at", "kind", "title", "description", "actor")
    verbose_name_plural = "تایم‌لاین سفارش"
    tab = True
    per_page = 8

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("number", "company", "po_number", "project_name", "amount_col", "status_badge",
                    "payment_badge", "credit_col", "approval_col", "rep_name", "ordered_at_col")
    list_display_links = ("number", "company")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("payment_method", ChoicesDropdownFilter),
        ("shipping_method", ChoicesDropdownFilter),
        ("company", RelatedDropdownFilter),
        ("sales_rep", RelatedDropdownFilter),
        ("ordered_at", RangeDateFilter),
        "placed_by_rep_for_company",
    )
    search_fields = ("number", "company__name", "po_number", "project_name", "waybill_number",
                     "internal_note")
    # ستونهای کارشناس/مشتری/اعتبار از این روابط میخوانند.
    list_select_related = ("company", "contact", "sales_rep", "shipping_address")
    autocomplete_fields = ("company", "contact", "sales_rep", "shipping_address")
    inlines = [OrderLineInline, ApprovalInline, OrderEventInline]
    readonly_fields = ("totals_display", "credit_display", "margin_display", "shipping_display",
                       "ordered_at", "updated_at")
    actions = ["action_reserve", "action_mark_ready", "action_deliver", "action_cancel"]
    actions_detail = ["reserve_stock_detail", "ship_detail", "create_invoice_detail", "deliver_detail"]
    fieldsets = (
        ("شناسه سفارش", {
            "fields": (("number", "status"), ("company", "contact"),
                       ("po_number", "project_name"), ("sales_rep",),
                       "placed_by_rep_for_company"),
        }),
        ("مبالغ و اعتبار", {
            "fields": ("totals_display", "credit_display", "margin_display", "discount_pct"),
        }),
        ("پرداخت و تسویه", {"fields": ("payment_method", "payment_terms")}),
        ("حمل و تحویل", {
            "fields": ("shipping_method", "shipping_cost", "shipping_address",
                       ("waybill_number", "carrier_name"), "expected_delivery_at",
                       "shipping_display"),
        }),
        ("یادداشت‌ها", {"fields": ("customer_note", "internal_note", "cancel_reason")}),
        ("زمان‌ها و ردیابی", {
            "fields": (("ordered_at", "approved_at"), ("shipped_at", "delivered_at"),
                       "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ------------------------------------------------------- ستون‌ها
    @admin.display(description="مبلغ", ordering="id")
    def amount_col(self, obj):
        return money_compact(obj.total)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="پرداخت", ordering="payment_method")
    def payment_badge(self, obj):
        return badge(obj.get_payment_method_display(), key="violet")

    @admin.display(description="اعتبار مشتری")
    def credit_col(self, obj):
        info = obj.credit_info
        if not info["limit"]:
            return badge("نقدی", key="muted")
        if info["exceeded"]:
            return badge("عبور از سقف اعتبار", key="danger")
        return progress_bar(info["usage_pct"],
                            DANGER if info["usage_pct"] >= 100 else ACCENT)

    @admin.display(description="تأیید")
    def approval_col(self, obj):
        """شمارش مرحله‌های تأیید از روی داده‌ی پیش‌واکشی‌شده.

        get_queryset این ادمین approvals را prefetch می‌کند؛ پس شمارش در پایتون
        انجام می‌شود و هیچ کوئری‌ای در هر ردیف اجرا نمی‌شود (پیش‌تر دو COUNT
        جداگانه در هر ردیف می‌رفت).
        """
        approvals = list(obj.approvals.all())
        pending = sum(1 for a in approvals if a.status == "pending")
        if pending:
            return badge(f"{num(pending)} مرحله در انتظار", key="warn")
        if any(a.status == "approved" for a in approvals):
            return badge("تأییدشده", key="ok")
        return badge("بدون نیاز به تأیید", key="muted")

    @admin.display(description="کارشناس", ordering="sales_rep__first_name")
    def rep_name(self, obj):
        if not obj.sales_rep_id:
            return "—"
        name = obj.sales_rep.get_full_name() or obj.sales_rep.username
        if obj.placed_by_rep_for_company:
            return format_html("{} <span style='font-size:11.5px;color:var(--panel-text-muted)'>(به‌نیابت)</span>", name)
        return name

    @admin.display(description="تاریخ ثبت", ordering="ordered_at")
    def ordered_at_col(self, obj):
        return jalali_dt(obj.ordered_at, "%Y/%m/%d")

    # ------------------------------------------------------- readonly
    @admin.display(description="جمع‌بندی مبالغ")
    def totals_display(self, obj):
        if not obj.pk:
            return "—"
        rows = [
            ["جمع اقلام", num(obj.subtotal, 0)],
            [f"تخفیف ({num(obj.discount_pct, 2)}٪)", num(obj.discount_amount, 0)],
            ["هزینه حمل", num(obj.shipping_cost, 0)],
            ["ارزش افزوده", num(obj.vat, 0)],
            ["مبلغ نهایی", f"<b>{num(obj.total, 0)} تومان</b>"],
            ["پرداخت‌شده / مانده", f"{num(obj.paid_amount, 0)} / {num(obj.balance, 0)}"],
        ]
        return html_table(["شرح", "مبلغ (تومان)"], rows)

    @admin.display(description="وضعیت اعتبار مشتری")
    def credit_display(self, obj):
        if not obj.pk:
            return "—"
        info = obj.credit_info
        label, color = obj.company.credit_status
        rows = [
            ["سقف اعتبار", num(info["limit"], 0)],
            ["مصرف‌شده", num(info["used"], 0)],
            ["اعتبار آزاد", num(info["available"], 0)],
            ["مبلغ این سفارش", num(obj.total, 0)],
        ]
        note = ""
        if info["exceeded"]:
            note = format_html(
                '<div class="panel-callout panel-callout--danger" style="margin-top:8px">'
                'مبلغ سفارش از اعتبار آزاد بیشتر است؛ '
                'نیاز به تأیید مالی یا دریافت پیش‌پرداخت دارد.</div>')
        return format_html("{}<div style='margin-top:8px'>{}</div>{}", badge(label, color=color),
                           html_table(["شرح", "مبلغ (تومان)"], rows), note)

    @admin.display(description="حاشیه سود ناخالص")
    def margin_display(self, obj):
        if not obj.pk:
            return "—"
        margin = obj.profit_margin_pct
        if margin is None:
            return badge("بهای تمام‌شده ثبت نشده", key="muted")
        key = "ok" if margin >= 20 else ("warn" if margin >= 10 else "danger")
        return badge(f"{num(margin, 1)}٪", key=key)

    @admin.display(description="وضعیت ارسال")
    def shipping_display(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            "{} — بارنامه: {} — تحویل تعهدی: {}",
            badge(obj.get_shipping_method_display(), key="info"),
            obj.waybill_number or "—",
            jalali(obj.expected_delivery_at) if obj.expected_delivery_at else "—",
        )

    # ------------------------------------------------------- اکشن‌های گروهی
    @admin.action(description="رزرو موجودی")
    def action_reserve(self, request, queryset):
        from .services import reserve_stock

        count = 0
        for order in queryset.filter(status__in=["draft", "approved"]):
            reserve_stock(order, user=request.user)
            count += 1
        self.message_user(request, f"{num(count)} سفارش رزرو شد.", messages.SUCCESS)

    @admin.action(description="علامت‌گذاری آماده ارسال")
    def action_mark_ready(self, request, queryset):
        from .services import mark_ready

        for order in queryset.filter(status="reserved"):
            mark_ready(order, user=request.user)

    @admin.action(description="ثبت تحویل به مشتری")
    def action_deliver(self, request, queryset):
        from .services import deliver

        for order in queryset.filter(status="shipped"):
            deliver(order, user=request.user)
        self.message_user(request, "سفارش‌های انتخابی تحویل‌شده ثبت شدند.", messages.SUCCESS)

    @admin.action(description="لغو سفارش (با آزادسازی رزرو)")
    def action_cancel(self, request, queryset):
        from .services import cancel

        for order in queryset.exclude(status__in=["delivered", "closed", "cancelled"]):
            cancel(order, user=request.user, reason="لغو از پنل")
        self.message_user(request, "سفارش‌های انتخابی لغو و رزرو آزاد شد.", messages.WARNING)

    # ------------------------------------------------------- اکشن‌های جزئیات
    @action(description="رزرو موجودی", icon="inventory_2", variant=ActionVariant.PRIMARY,
            permissions=["change"])
    def reserve_stock_detail(self, request, object_id):
        from .services import reserve_stock

        order = Order.objects.get(pk=object_id)
        reserve_stock(order, user=request.user)
        messages.success(request, f"موجودی سفارش {order.number} رزرو شد.")
        return redirect(reverse("admin:orders_order_change", args=[object_id]))

    @action(description="ثبت ارسال", icon="local_shipping", permissions=["change"])
    def ship_detail(self, request, object_id):
        from .services import ship

        order = Order.objects.get(pk=object_id)
        ship(order, user=request.user, waybill=order.waybill_number, carrier=order.carrier_name)
        messages.success(request, f"ارسال سفارش {order.number} ثبت و موجودی کسر شد.")
        return redirect(reverse("admin:orders_order_change", args=[object_id]))

    @action(description="صدور فاکتور", icon="receipt_long", variant=ActionVariant.PRIMARY,
            permissions=["change"])
    def create_invoice_detail(self, request, object_id):
        from .services import create_invoice

        order = Order.objects.get(pk=object_id)
        invoice = create_invoice(order, user=request.user)
        messages.success(request, f"فاکتور {invoice.number} صادر شد.")
        return redirect(reverse("admin:finance_invoice_change", args=[invoice.pk]))

    @action(description="ثبت تحویل", icon="check_circle", variant=ActionVariant.SUCCESS,
            permissions=["change"])
    def deliver_detail(self, request, object_id):
        from .services import deliver

        order = Order.objects.get(pk=object_id)
        deliver(order, user=request.user)
        messages.success(request, f"تحویل سفارش {order.number} ثبت شد.")
        return redirect(reverse("admin:orders_order_change", args=[object_id]))

    # ------------------------------------------------------- دسترسی
    def get_queryset(self, request):
        qs = (super().get_queryset(request)
              .select_related("company", "sales_rep")
              .prefetch_related("lines__product", "approvals"))
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "sales":
            qs = qs.filter(company__sales_rep=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "scope_badge", "threshold_col", "approver_role", "step", "is_active")
    list_filter = (("scope", ChoicesDropdownFilter), ("approver_role", ChoicesDropdownFilter),
                   "is_active")
    search_fields = ("name", "note")
    ordering = ("scope", "step")

    @admin.display(description="دامنه", ordering="scope")
    def scope_badge(self, obj):
        return badge(obj.get_scope_display(), key="primary")

    @admin.display(description="آستانه", ordering="threshold")
    def threshold_col(self, obj):
        if obj.scope == "discount_pct":
            return badge(f"{num(obj.threshold, 0)}٪", key="warn")
        return money_compact(obj.threshold)


@admin.register(Approval)
class ApprovalAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("order", "step", "required_role", "status_badge", "approver", "amount_col",
                    "comment", "acted_at_col")
    list_filter = (("status", ChoicesDropdownFilter), ("required_role", ChoicesDropdownFilter),
                   ("order__status", ChoicesDropdownFilter))
    search_fields = ("order__number", "order__company__name", "comment")
    autocomplete_fields = ("order", "approver", "rule")
    actions = ["action_approve_selected", "action_reject_selected"]
    actions_row = ["approve_row", "reject_row"]

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="مبلغ سفارش")
    def amount_col(self, obj):
        return money_compact(obj.amount_snapshot)

    @admin.display(description="زمان اقدام", ordering="acted_at")
    def acted_at_col(self, obj):
        return jalali_dt(obj.acted_at) if obj.acted_at else "—"

    @admin.action(description="تأیید مراحل انتخابی")
    def action_approve_selected(self, request, queryset):
        from .services import approve

        for approval in queryset.filter(status="pending").select_related("order"):
            approve(approval, request.user, comment="تأیید گروهی از پنل")
        self.message_user(request, "مراحل انتخابی تأیید شد.", messages.SUCCESS)

    @admin.action(description="رد مراحل انتخابی")
    def action_reject_selected(self, request, queryset):
        from .services import reject

        for approval in queryset.filter(status="pending").select_related("order"):
            reject(approval, request.user, reason="رد گروهی از پنل")
        self.message_user(request, "مراحل انتخابی رد شد.", messages.WARNING)

    @action(description="تأیید", icon="check", variant=ActionVariant.SUCCESS, permissions=["change"])
    def approve_row(self, request, object_id):
        from .services import approve

        approval = Approval.objects.select_related("order").get(pk=object_id)
        order = approve(approval, request.user, comment="تأیید از لیست کارتابل")
        messages.success(request, f"مرحله تأیید شد — وضعیت سفارش {order.number}: {order.get_status_display()}")
        return redirect(reverse("admin:orders_approval_changelist"))

    @action(description="رد", icon="close", variant=ActionVariant.DANGER, permissions=["change"])
    def reject_row(self, request, object_id):
        from .services import reject

        approval = Approval.objects.select_related("order").get(pk=object_id)
        reject(approval, request.user, reason="رد از کارتابل تأیید")
        messages.warning(request, f"مرحله رد شد — سفارش {approval.order.number} به پیش‌نویس برگشت.")
        return redirect(reverse("admin:orders_approval_changelist"))


# =========================================================== ثبت مستقل ردیف‌ها و تایم‌لاین
@admin.register(OrderLine)
class OrderLineAdmin(PanelModelAdmin, ModelAdmin):
    """ردیف‌های سفارش — در حالت عادی داخل صفحه سفارش ویرایش می‌شوند،
    این صفحه برای جست‌وجو و گزارش‌گیری سراسری روی ردیف‌هاست."""

    list_display = ("order_col", "product_col", "qty_col", "price_col", "discount_col",
                    "reserved_col", "shipped_col", "warehouse")
    list_select_related = ("order", "product", "warehouse")
    search_fields = ("order__number", "product__code", "product__name", "order__company__name")
    list_filter = (("warehouse", RelatedDropdownFilter), "product__category", "order__status")
    autocomplete_fields = ("order", "product", "warehouse")
    list_per_page = 40
    fieldsets = (
        ("ردیف", {"fields": ("order", "product", "warehouse", "spec_note")}),
        ("مقدار و قیمت", {"fields": ("qty", "unit_price", "discount_pct")}),
        ("تأمین و حمل", {"fields": ("qty_reserved", "qty_shipped", "lead_time_days")}),
        ("بهای تمام‌شده", {"fields": ("list_price", "unit_cost"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "product", "warehouse")

    @admin.display(description="سفارش", ordering="order__number")
    def order_col(self, obj):
        return format_html('<a class="panel-mono" href="/admin/orders/order/{}/change/">{}</a>',
                           obj.order_id, obj.order.number)

    @admin.display(description="کالا", ordering="product__code")
    def product_col(self, obj):
        return format_html("{}<div class=\"panel-mono\">{}</div>", obj.product.name, obj.product.code)

    @admin.display(description="مقدار", ordering="qty")
    def qty_col(self, obj):
        return f"{num(obj.qty)} {obj.product.get_uom_display()}"

    @admin.display(description="مبلغ واحد", ordering="unit_price")
    def price_col(self, obj):
        return money_compact(obj.unit_price)

    @admin.display(description="تخفیف", ordering="discount_pct")
    def discount_col(self, obj):
        return badge(f"{num(obj.discount_pct)}٪", COLORS["warn"] if obj.discount_pct else COLORS["muted"])

    @admin.display(description="رزرو", ordering="qty_reserved")
    def reserved_col(self, obj):
        return num(obj.qty_reserved)

    @admin.display(description="ارسال‌شده", ordering="qty_shipped")
    def shipped_col(self, obj):
        return num(obj.qty_shipped)


@admin.register(OrderEvent)
class OrderEventAdmin(PanelModelAdmin, ModelAdmin):
    """تایم‌لاین سفارش‌ها — فقط‌خواندنی؛ ثبت رخداد از طریق سرویس‌ها انجام می‌شود."""

    list_display = ("created_col", "order_col", "kind_badge", "title", "actor", "short_description")
    list_select_related = ("order", "actor")
    search_fields = ("order__number", "order__company__name", "title", "description")
    list_filter = (("kind", ChoicesDropdownFilter), ("actor", RelatedDropdownFilter),
                   ("created_at", RangeDateFilter))
    list_per_page = 40
    ordering = ("-created_at",)

    KIND_COLORS = {
        "status": COLORS["info"], "approval": COLORS["primary"], "reject": COLORS["danger"],
        "stock": COLORS["warn"], "ship": COLORS["violet"], "delivery": COLORS["ok"],
        "invoice": COLORS["warn"], "commitment": COLORS["violet"], "note": COLORS["muted"],
        "cancel": COLORS["danger"],
    }

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(description="زمان", ordering="created_at")
    def created_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.display(description="سفارش", ordering="order__number")
    def order_col(self, obj):
        return format_html('<a class="panel-mono" href="/admin/orders/order/{}/change/">{}</a>',
                           obj.order_id, obj.order.number)

    @admin.display(description="نوع رخداد", ordering="kind")
    def kind_badge(self, obj):
        return badge(obj.get_kind_display(), self.KIND_COLORS.get(obj.kind, COLORS["muted"]))

    @admin.display(description="توضیح")
    def short_description(self, obj):
        return obj.description[:80] or "—"
