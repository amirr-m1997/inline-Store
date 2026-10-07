"""ادمین استعلام قیمت (RFQ) و پیام‌های مذاکره."""
from __future__ import annotations

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.enums import ActionVariant
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)

from core.admin_utils import COLORS, PanelModelAdmin, badge, html_table, money_compact
from core.utils import jalali, jalali_dt, num
from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter

from .models import Quote, QuoteLine, QuoteMessage


class QuoteLineInline(TabularInline):
    model = QuoteLine
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("product", "qty", "list_price", "offered_price", "discount_pct",
              "lead_time_days", "availability_note", "note")
    readonly_fields = ("list_price",)
    verbose_name_plural = "ردیف‌های پیشنهاد"
    tab = True


class QuoteMessageInline(TabularInline):
    model = QuoteMessage
    extra = 0
    fields = ("kind", "is_internal", "body", "author", "created_at")
    readonly_fields = ("created_at",)
    verbose_name_plural = "گفت‌وگوی مذاکره"
    tab = True


@admin.register(Quote)
class QuoteAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("company", "assigned_to", "contact", "created_by")
    list_display = ("number", "company", "project_name", "items_summary", "total_col",
                    "status_badge", "priority_badge", "assigned_to", "sla_col", "validity_col")
    list_display_links = ("number", "company")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("priority", ChoicesDropdownFilter),
        ("assigned_to", RelatedDropdownFilter),
        ("company", RelatedDropdownFilter),
        ("source", ChoicesDropdownFilter),
        ("created_at", RangeDateFilter),
    )
    search_fields = ("number", "company__name", "project_name", "customer_note", "internal_note")
    autocomplete_fields = ("company", "contact", "assigned_to", "technical_reviewer", "order")
    inlines = [QuoteLineInline, QuoteMessageInline]
    readonly_fields = ("sla_status_display", "totals_display", "expiry_display", "created_at",
                       "updated_at", "first_response_at")
    actions = ["action_assign_me", "action_recalc_prices", "action_send_offer", "action_mark_lost"]
    actions_detail = ["convert_to_order_detail", "escalate_detail", "recalculate_detail"]
    fieldsets = (
        ("شناسه", {
            "fields": (("number", "status", "priority", "source"),
                       ("company", "contact", "project_name"),
                       ("assigned_to", "technical_reviewer")),
        }),
        ("مهلت و اعتبار", {"fields": (("sla_due_at", "first_response_at"), "valid_until", "sla_status_display")}),
        ("شرایط", {
            "fields": (("discount_pct", "delivery_days"),
                       ("payment_terms", "delivery_terms")),
        }),
        ("مبالغ", {"fields": ("totals_display", "expiry_display")}),
        ("یادداشت‌ها", {
            "fields": ("customer_note", "internal_note"),
            "description": "یادداشت داخلی هرگز برای مشتری نمایش داده نمی‌شود.",
        }),
        ("نتیجه", {"fields": ("order", "lost_reason", "version", "created_by",
                              "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # -------------------------------------------------------- ستون‌ها
    @admin.display(description="اقلام")
    def items_summary(self, obj):
        count = obj.lines.count()
        return format_html(
            '<span style="font-size:12px">{}</span><div style="font-size:11px;color:var(--panel-text-muted)">{} قلم</div>',
            (obj.items_summary or "—")[:60], num(count),
        )

    @admin.display(description="مبلغ پیشنهادی")
    def total_col(self, obj):
        if not obj.lines.exists():
            return badge("بدون قیمت", key="warn")
        return money_compact(obj.total)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return badge(obj.get_status_display(), color=obj.status_color)

    @admin.display(description="اولویت", ordering="priority")
    def priority_badge(self, obj):
        return badge(obj.get_priority_display(),
                     key={"urgent": "danger", "normal": "primary", "project": "violet"}[obj.priority])

    @admin.display(description="مهلت SLA (ساعت)", ordering="sla_due_at")
    def sla_col(self, obj):
        if not obj.sla_due_at:
            return "—"
        if not obj.is_open:
            return badge("بسته‌شده", key="muted")
        if obj.is_sla_overdue:
            hours = abs(obj.sla_remaining_hours or 0)
            return badge(f"منقضی ({num(hours, 1)} ساعت)", key="danger")
        remaining = obj.sla_remaining_hours or 0
        key = "warn" if remaining <= 8 else "ok"
        return badge(f"{num(remaining, 1)} ساعت", key=key)

    @admin.display(description="اعتبار قیمت", ordering="valid_until")
    def validity_col(self, obj):
        if not obj.valid_until:
            return "—"
        days = obj.days_to_expiry
        if days is None:
            return "—"
        if days < 0:
            return badge("منقضی", key="danger")
        key = "warn" if days <= 5 else "ok"
        return badge(f"{num(days)} روز ({jalali(obj.valid_until)})", key=key)

    # -------------------------------------------------------- readonly
    @admin.display(description="وضعیت SLA")
    def sla_status_display(self, obj):
        if not obj.pk:
            return "—"
        if obj.first_response_at:
            delta = obj.first_response_at - obj.created_at
            hours = round(delta.total_seconds() / 3600, 1)
            return format_html("{} — اولین پاسخ پس از {} ساعت",
                               badge("پاسخ داده‌شده", key="ok"), num(hours, 1))
        if obj.is_sla_overdue:
            return badge("از SLA عبور کرده — نیاز به اقدام فوری", key="danger")
        return badge(f"{num(obj.sla_remaining_hours or 0, 1)} ساعت تا مهلت", key="warn")

    @admin.display(description="جمع‌بندی مبالغ")
    def totals_display(self, obj):
        if not obj.pk:
            return "—"
        rows = [
            ["جمع اقلام", num(obj.subtotal, 0)],
            [f"تخفیف ({num(obj.discount_pct, 2)}٪)", num(obj.discount_amount, 0)],
            [f"ارزش افزوده ({num(9)}٪)", num(obj.vat, 0)],
            ["مبلغ نهایی", f"<b>{num(obj.total, 0)} تومان</b>"],
        ]
        return html_table(["شرح", "مبلغ"], rows)

    @admin.display(description="نسخه و اعتبار")
    def expiry_display(self, obj):
        if not obj.pk:
            return "—"
        if not obj.valid_until:
            return badge(f"نسخه {num(obj.version)} — بدون تاریخ انقضا", key="muted")
        return badge(f"نسخه {num(obj.version)} — اعتبار تا {jalali(obj.valid_until)}",
                     key="ok" if (obj.days_to_expiry or 0) > 0 else "danger")

    # -------------------------------------------------------- اکشن‌ها
    @admin.action(description="ارجاع به من (کاربر جاری)")
    def action_assign_me(self, request, queryset):
        from .services import assign

        for quote in queryset:
            assign(quote, request.user, actor=request.user)
        self.message_user(request, f"{num(queryset.count())} استعلام به شما ارجاع شد.", messages.SUCCESS)

    @admin.action(description="محاسبه مجدد قیمت‌ها (بر اساس سبد مشتری)")
    def action_recalc_prices(self, request, queryset):
        from .services import recalc_prices

        for quote in queryset:
            recalc_prices(quote)
        self.message_user(request, f"قیمت {num(queryset.count())} استعلام بازمحاسبه شد.", messages.SUCCESS)

    @admin.action(description="ارسال پیش‌فاکتور به مشتری")
    def action_send_offer(self, request, queryset):
        from .services import send_offer

        sent = 0
        for quote in queryset:
            if not quote.lines.exists():
                continue
            send_offer(quote, user=request.user)
            sent += 1
        self.message_user(request, f"{num(sent)} پیش‌فاکتور ارسال شد.", messages.SUCCESS)

    @admin.action(description="ثبت به‌عنوان از دست رفته")
    def action_mark_lost(self, request, queryset):
        queryset.update(status="lost")
        self.message_user(request, "وضعیت به «از دست رفته» تغییر کرد.", messages.WARNING)

    # -------------------------------------------------------- اکشن‌های صفحه جزئیات
    @action(description="تبدیل به سفارش", icon="shopping_cart",
            variant=ActionVariant.PRIMARY, permissions=["change"])
    def convert_to_order_detail(self, request, object_id):
        from django.shortcuts import redirect

        from .services import convert_to_order

        quote = Quote.objects.select_related("company").get(pk=object_id)
        order = convert_to_order(quote, user=request.user)
        messages.success(request, f"سفارش {order.number} از استعلام ساخته شد و در گردش تأیید قرار گرفت.")
        return redirect(reverse("admin:orders_order_change", args=[order.pk]))

    @action(description="اولویت فوری", icon="priority_high",
            variant=ActionVariant.WARNING, permissions=["change"])
    def escalate_detail(self, request, object_id):
        from django.shortcuts import redirect

        from django.utils import timezone

        quote = Quote.objects.get(pk=object_id)
        quote.priority = "urgent"
        quote.sla_due_at = timezone.now() + timezone.timedelta(hours=4)
        quote.save(update_fields=["priority", "sla_due_at"])
        messages.warning(request, f"اولویت {quote.number} به «فوری» تغییر کرد (SLA: ۴ ساعت).")
        return redirect(reverse("admin:quotes_quote_change", args=[object_id]))

    @action(description="محاسبه مجدد قیمت", icon="calculate", permissions=["change"])
    def recalculate_detail(self, request, object_id):
        from django.shortcuts import redirect

        from .services import recalc_prices

        quote = Quote.objects.get(pk=object_id)
        recalc_prices(quote)
        messages.success(request, f"قیمت‌های {quote.number} بازمحاسبه شد (نسخه {quote.version}).")
        return redirect(reverse("admin:quotes_quote_change", args=[object_id]))

    # -------------------------------------------------------- دسترسی
    def get_queryset(self, request):
        qs = (super().get_queryset(request)
              .select_related("company", "assigned_to", "order")
              .prefetch_related("lines__product"))
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "sales":
            qs = qs.filter(company__sales_rep=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuoteLine)
class QuoteLineAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("quote", "product", "quote__company")
    list_display = ("quote", "product", "qty", "list_price_col", "offered_price_col",
                    "discount_col", "lead_time_col", "line_total_col")
    list_filter = (("product__category", RelatedDropdownFilter),
                   ("quote__status", ChoicesDropdownFilter))
    search_fields = ("quote__number", "product__code", "product__name")
    autocomplete_fields = ("quote", "product")
    actions = ["action_apply_pricing"]

    @admin.display(description="قیمت لیست")
    def list_price_col(self, obj):
        return money_compact(obj.list_price)

    @admin.display(description="قیمت پیشنهادی", ordering="offered_price")
    def offered_price_col(self, obj):
        return money_compact(obj.offered_price)

    @admin.display(description="تخفیف", ordering="discount_pct")
    def discount_col(self, obj):
        pct = float(obj.discount_pct or 0)
        return badge(f"{num(pct, 1)}٪", key="warn" if pct > 10 else ("ok" if pct else "muted"))

    @admin.display(description="زمان تأمین")
    def lead_time_col(self, obj):
        return badge(f"{num(obj.lead_time_days)} روز", key="primary") if obj.lead_time_days else "—"

    @admin.display(description="جمع ردیف")
    def line_total_col(self, obj):
        return money_compact(obj.line_total)

    @admin.action(description="تعیین قیمت از موتور قیمت‌گذاری")
    def action_apply_pricing(self, request, queryset):
        for line in queryset.select_related("product", "quote__company"):
            line.apply_price(company=line.quote.company)
        self.message_user(request, f"قیمت {num(queryset.count())} ردیف بازمحاسبه شد.", messages.SUCCESS)


@admin.register(QuoteMessage)
class QuoteMessageAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("quote", "author", "quote__company")
    list_display = ("quote", "kind", "internal_badge", "display_author", "created_at_col", "short_body")
    list_filter = (("kind", ChoicesDropdownFilter), "is_internal", ("quote__status", ChoicesDropdownFilter))
    search_fields = ("quote__number", "body", "author_name")
    autocomplete_fields = ("quote", "author")

    @admin.display(description="محرمانگی")
    def internal_badge(self, obj):
        return badge("یادداشت داخلی", key="warn") if obj.is_internal else badge("قابل نمایش به مشتری", key="ok")

    @admin.display(description="زمان", ordering="created_at")
    def created_at_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.display(description="متن")
    def short_body(self, obj):
        return (obj.body or "")[:80]
