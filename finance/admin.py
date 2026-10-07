"""ادمین مالی: فاکتور (و مؤدیان)، پرداخت و چک."""
from __future__ import annotations

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)
from unfold.decorators import action
from unfold.enums import ActionVariant

from core.admin_utils import COLORS, PanelModelAdmin, badge, html_table, money_compact
from core.utils import jalali, jalali_dt, num
from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter

from .models import Cheque, Invoice, InvoiceLine, Payment


class InvoiceLineInline(TabularInline):
    model = InvoiceLine
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("title", "product", "qty", "unit_price", "discount_pct")
    verbose_name_plural = "ردیف‌های فاکتور"
    tab = True


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    fk_name = "invoice"
    fields = ("method", "amount", "paid_at", "bank", "reference", "note")
    verbose_name_plural = "پرداخت‌های این فاکتور"
    tab = True


class ChequeInline(TabularInline):
    model = Cheque
    extra = 0
    fk_name = "invoice"
    fields = ("number", "bank", "amount", "due_date", "status")
    verbose_name_plural = "چک‌های مرتبط"
    tab = True


@admin.register(Invoice)
class InvoiceAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("company", "order", "created_by")
    list_display = ("number", "kind_badge", "company", "total_col", "balance_col", "status_badge",
                    "moadian_badge", "issued_col", "due_col", "overdue_col")
    list_display_links = ("number", "company")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("moadian_status", ChoicesDropdownFilter),
        ("kind", ChoicesDropdownFilter),
        ("company", RelatedDropdownFilter),
        ("issued_at", RangeDateFilter),
    )
    search_fields = ("number", "company__name", "moadian_tax_id", "note")
    autocomplete_fields = ("company", "order")
    inlines = [InvoiceLineInline, PaymentInline, ChequeInline]
    # مبالغ فاکتور فقط از راه سرویس‌های مالی (ثبت پرداخت، گردش سفارش) تغییر می‌کنند
    readonly_fields = ("amounts_display", "moadian_display", "created_at",
                       "subtotal", "discount_amount", "vat_amount", "shipping_amount",
                       "total", "paid_amount")
    actions = ["action_submit_moadian", "action_mark_overdue", "action_mark_accepted"]
    actions_detail = ["submit_moadian_detail", "register_payment_detail"]
    fieldsets = (
        ("شناسه", {"fields": (("number", "kind", "status"), ("company", "order"),
                              ("issued_at", "due_date", "settled_at"))}),
        ("مبالغ", {"fields": ("amounts_display", ("discount_amount", "shipping_amount"))}),
        ("سامانه مؤدیان", {
            "fields": ("moadian_display", ("moadian_status", "moadian_tax_id"),
                       ("moadian_sent_at", "buyer_economic_code"), "moadian_error"),
            "description": "صورتحساب الکترونیکی الزام قانونی است؛ ارسال از طریق نرم‌افزار واسط "
                           "مورد تأیید سازمان مالیاتی انجام می‌شود.",
        }),
        ("یادداشت", {"fields": ("note", "created_by", "created_at"), "classes": ("collapse",)}),
    )

    # -------------------------------------------------------- ستون‌ها
    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        return badge(obj.get_kind_display(),
                     key="primary" if obj.kind == "official" else "violet")

    @admin.display(description="مبلغ کل", ordering="total")
    def total_col(self, obj):
        return money_compact(obj.total)

    @admin.display(description="مانده")
    def balance_col(self, obj):
        if not obj.balance:
            return badge("تسویه‌شده", key="ok")
        return money_compact(obj.balance)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="مؤدیان", ordering="moadian_status")
    def moadian_badge(self, obj):
        return badge(obj.get_moadian_status_display(), color=obj.moadian_color)

    @admin.display(description="تاریخ صدور", ordering="issued_at")
    def issued_col(self, obj):
        return jalali(obj.issued_at)

    @admin.display(description="سررسید", ordering="due_date")
    def due_col(self, obj):
        return jalali(obj.due_date) if obj.due_date else "—"

    @admin.display(description="تأخیر")
    def overdue_col(self, obj):
        days = obj.days_overdue
        if not days:
            return "—"
        key = "danger" if days > 30 else "warn"
        return badge(f"{num(days)} روز", key=key)

    # -------------------------------------------------------- readonly
    @admin.display(description="جمع‌بندی مالی")
    def amounts_display(self, obj):
        if not obj.pk:
            return "—"
        rows = [
            ["جمع اقلام", num(obj.subtotal, 0)],
            ["تخفیف", num(obj.discount_amount, 0)],
            ["هزینه حمل", num(obj.shipping_amount, 0)],
            ["ارزش افزوده", num(obj.vat_amount, 0)],
            ["مبلغ کل", f"<b>{num(obj.total, 0)}</b>"],
            ["پرداخت‌شده", num(obj.paid_amount, 0)],
            ["مانده", f"<b>{num(obj.balance, 0)}</b>"],
        ]
        return html_table(["شرح", "تومان"], rows)

    @admin.display(description="وضعیت ارسال به مؤدیان")
    def moadian_display(self, obj):
        if not obj.pk:
            return "—"
        from .services import validate_for_moadian

        errors = validate_for_moadian(obj)
        if errors:
            items = "".join(f"<li>{e}</li>" for e in errors)
            return format_html(
                '<div style="padding:9px 11px;background:#fdecec;border:1px solid #f6d3d3;'
                'border-radius:10px;color:#8f1d1d;font-size:12px">'
                '<b>خطاهای اعتبارسنجی پیش از ارسال:</b><ul style="margin:6px 0 0">{}</ul></div>', 
                format_html(items),
            )
        if obj.moadian_status == "submitted":
            return badge(f"ارسال شد — شناسه مالیاتی: {obj.moadian_tax_id}", key="ok")
        return badge("آماده ارسال (بدون خطای اعتبارسنجی)", key="primary")

    # -------------------------------------------------------- اکشن‌ها
    @admin.action(description="ارسال به سامانه مؤدیان")
    def action_submit_moadian(self, request, queryset):
        from .services import submit_to_moadian

        ok, failed = 0, 0
        for invoice in queryset:
            submit_to_moadian(invoice, user=request.user)
            if invoice.moadian_status == "submitted":
                ok += 1
            else:
                failed += 1
        if ok:
            self.message_user(request, f"{num(ok)} فاکتور با موفقیت ارسال شد.", messages.SUCCESS)
        if failed:
            self.message_user(request, f"{num(failed)} فاکتور خطای اعتبارسنجی دارد.", messages.ERROR)

    @admin.action(description="علامت‌گذاری معوق")
    def action_mark_overdue(self, request, queryset):
        count = queryset.exclude(status__in=["paid", "cancelled"]).filter(
            due_date__lt=timezone.localdate()).update(status="overdue")
        self.message_user(request, f"{num(count)} فاکتور معوق علامت خورد.", messages.WARNING)

    @admin.action(description="ثبت پذیرش در مؤدیان")
    def action_mark_accepted(self, request, queryset):
        count = queryset.filter(moadian_status="submitted").update(moadian_status="accepted",
                                                                   status="accepted")
        self.message_user(request, f"{num(count)} فاکتور به‌عنوان پذیرفته‌شده در سامانه ثبت شد.",
                          messages.SUCCESS)

    # -------------------------------------------------------- اکشن جزئیات
    @action(description="ارسال به مؤدیان", icon="send", variant=ActionVariant.PRIMARY,
            permissions=["change"])
    def submit_moadian_detail(self, request, object_id):
        from .services import submit_to_moadian

        invoice = Invoice.objects.get(pk=object_id)
        submit_to_moadian(invoice, user=request.user)
        if invoice.moadian_status == "submitted":
            messages.success(request, f"فاکتور {invoice.number} به مؤدیان ارسال شد "
                                      f"(شناسه مالیاتی {invoice.moadian_tax_id}).")
        else:
            messages.error(request, f"ارسال ناموفق: {invoice.moadian_error}")
        return redirect(reverse("admin:finance_invoice_change", args=[object_id]))

    @action(description="ثبت پرداخت", icon="payments", permissions=["change"])
    def register_payment_detail(self, request, object_id):
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(
            reverse("admin:finance_payment_add") + f"?invoice={object_id}")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "order")


@admin.register(Payment)
class PaymentAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("invoice", "invoice__company", "company", "created_by")
    list_display = ("paid_at_col", "company", "method_badge", "amount_col", "invoice_link",
                    "order_link", "bank", "reference", "created_by")
    list_filter = (("method", ChoicesDropdownFilter), ("company", RelatedDropdownFilter),
                   ("paid_at", RangeDateFilter))
    search_fields = ("company__name", "reference", "bank", "note", "invoice__number")
    autocomplete_fields = ("company", "invoice", "order")
    fieldsets = (
        ("پرداخت", {"fields": ("company", "method", "amount", "paid_at")}),
        ("ارجاع", {"fields": ("invoice", "order", "bank", "reference")}),
        ("توضیح", {"fields": ("note", "created_by")}),
    )

    @admin.display(description="تاریخ", ordering="paid_at")
    def paid_at_col(self, obj):
        return jalali(obj.paid_at)

    @admin.display(description="روش", ordering="method")
    def method_badge(self, obj):
        return badge(obj.get_method_display(), key="primary")

    @admin.display(description="مبلغ", ordering="amount")
    def amount_col(self, obj):
        return money_compact(obj.amount)

    @admin.display(description="فاکتور")
    def invoice_link(self, obj):
        if not obj.invoice_id:
            return "—"
        url = reverse("admin:finance_invoice_change", args=[obj.invoice_id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.number)

    @admin.display(description="سفارش")
    def order_link(self, obj):
        if not obj.order_id:
            return "—"
        url = reverse("admin:orders_order_change", args=[obj.order_id])
        return format_html('<a href="{}">{}</a>', url, obj.order.number)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        obj.apply_to_invoice()


@admin.register(Cheque)
class ChequeAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("company", "order")
    list_display = ("number", "company", "direction_badge", "bank", "amount_col", "due_col",
                    "urgency_badge", "status_badge", "invoice_link")
    list_filter = (("status", ChoicesDropdownFilter), ("direction", ChoicesDropdownFilter),
                   ("bank", ChoicesDropdownFilter), ("company", RelatedDropdownFilter),
                   ("due_date", RangeDateFilter))
    search_fields = ("number", "company__name", "bank", "branch", "account_holder", "note")
    autocomplete_fields = ("company", "invoice", "order")
    actions = ["action_deposit", "action_clear", "action_bounce"]
    actions_detail = ["clear_detail"]
    readonly_fields = ("created_at",)
    fieldsets = (
        ("چک", {"fields": (("number", "direction"), ("company", "bank", "branch", "account_holder"),
                          ("amount", "issue_date", "due_date"))}),
        ("وضعیت و وصول", {"fields": ("status", ("deposited_at", "cleared_at"), "bounce_reason")}),
        ("ارجاع", {"fields": ("invoice", "order", "note")}),
        ("ردیابی", {"fields": ("created_by", "created_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="جهت", ordering="direction")
    def direction_badge(self, obj):
        return badge(obj.get_direction_display(),
                     key="ok" if obj.direction == "received" else "warn")

    @admin.display(description="مبلغ", ordering="amount")
    def amount_col(self, obj):
        return money_compact(obj.amount)

    @admin.display(description="سررسید", ordering="due_date")
    def due_col(self, obj):
        return jalali(obj.due_date)

    @admin.display(description="فاصله سررسید")
    def urgency_badge(self, obj):
        label, color = obj.urgency
        return badge(label, color=color)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="فاکتور")
    def invoice_link(self, obj):
        if not obj.invoice_id:
            return "—"
        url = reverse("admin:finance_invoice_change", args=[obj.invoice_id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.number)

    # -------------------------------------------------------- اکشن‌ها
    @admin.action(description="ثبت سپرده به بانک")
    def action_deposit(self, request, queryset):
        from .services import deposit_cheque

        count = 0
        for cheque in queryset.filter(status="in_hand"):
            deposit_cheque(cheque, user=request.user)
            count += 1
        self.message_user(request, f"{num(count)} چک سپرده‌شده ثبت شد.", messages.SUCCESS)

    @admin.action(description="ثبت وصول (و تسویه فاکتور مرتبط)")
    def action_clear(self, request, queryset):
        from .services import clear_cheque

        count = 0
        for cheque in queryset.filter(status__in=["in_hand", "deposited"]):
            clear_cheque(cheque, user=request.user)
            count += 1
        self.message_user(request, f"{num(count)} چک وصول شد و فاکتورهای مرتبط تسویه شدند.",
                          messages.SUCCESS)

    @admin.action(description="ثبت برگشت چک")
    def action_bounce(self, request, queryset):
        from .services import bounce_cheque

        count = 0
        for cheque in queryset.filter(status__in=["in_hand", "deposited"]):
            bounce_cheque(cheque, reason="برگشتی — پیگیری مالی", user=request.user)
            count += 1
        self.message_user(request, f"{num(count)} چک برگشتی ثبت شد.", messages.ERROR)

    @action(description="وصول چک", icon="check_circle", variant=ActionVariant.SUCCESS,
            permissions=["change"])
    def clear_detail(self, request, object_id):
        from .services import clear_cheque

        cheque = Cheque.objects.get(pk=object_id)
        clear_cheque(cheque, user=request.user)
        messages.success(request, f"چک {cheque.number} وصول و فاکتور مرتبط تسویه شد.")
        return redirect(reverse("admin:finance_cheque_change", args=[object_id]))

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =========================================================== ردیف‌های فاکتور (ثبت مستقل)
@admin.register(InvoiceLine)
class InvoiceLineAdmin(PanelModelAdmin, ModelAdmin):
    """ردیف‌های فاکتور — ویرایش معمول داخل صفحه فاکتور؛ این صفحه برای جست‌وجوی سراسری
    روی اقلام فروش‌رفته و مقایسه قیمت فاکتور با قیمت لیست است."""
    list_select_related = ("invoice", "product", "invoice__company")

    list_display = ("invoice_col", "title_col", "qty_col", "unit_price_col", "discount_col",
                    "line_total_col", "diff_col")
    list_select_related = ("invoice", "product")
    search_fields = ("invoice__number", "product__code", "title", "invoice__company__name")
    list_filter = (("invoice__kind", ChoicesDropdownFilter), ("invoice__status", ChoicesDropdownFilter),
                   ("product__category", RelatedDropdownFilter))
    autocomplete_fields = ("invoice", "product")
    list_per_page = 40

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("invoice", "product")

    @admin.display(description="فاکتور", ordering="invoice__number")
    def invoice_col(self, obj):
        return format_html('<a class="panel-mono" href="/admin/finance/invoice/{}/change/">{}</a>',
                           obj.invoice_id, obj.invoice.number)

    @admin.display(description="شرح / کالا", ordering="title")
    def title_col(self, obj):
        if obj.product_id:
            return format_html("{}<div class=\"panel-mono\">{}</div>", obj.title, obj.product.code)
        return obj.title

    @admin.display(description="مقدار", ordering="qty")
    def qty_col(self, obj):
        uom = obj.product.get_uom_display() if obj.product_id else ""
        return f"{num(obj.qty)} {uom}".strip()

    @admin.display(description="مبلغ واحد", ordering="unit_price")
    def unit_price_col(self, obj):
        return money_compact(obj.unit_price)

    @admin.display(description="تخفیف", ordering="discount_pct")
    def discount_col(self, obj):
        return badge(f"{num(obj.discount_pct)}٪", COLORS["warn"] if obj.discount_pct else COLORS["muted"])

    @admin.display(description="جمع ردیف")
    def line_total_col(self, obj):
        return money_compact(obj.line_total)

    @admin.display(description="اختلاف با قیمت لیست")
    def diff_col(self, obj):
        if not obj.product_id or not obj.product.base_price:
            return "—"
        diff = int(obj.unit_price) - int(obj.product.base_price)
        if diff == 0:
            return badge("برابر لیست", COLORS["muted"])
        pct = diff / float(obj.product.base_price) * 100
        color = COLORS["ok"] if diff < 0 else COLORS["danger"]
        return badge(f"{num(round(pct, 1))}٪", color)
