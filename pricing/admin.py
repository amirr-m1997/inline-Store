"""ادمین قیمت‌گذاری: سبد قیمت، اقلام قیمت و پله‌های حجمی."""
from __future__ import annotations

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.admin_utils import ModelHelpMixin, PanelModelAdmin, badge, diff_cell, html_table, money_compact
from core.utils import jalali, num

from .models import PriceList, PriceListItem, QuantityPriceBreak


class PriceListItemInline(TabularInline):
    model = PriceListItem
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("product", "price", "valid_from", "valid_until", "note")
    tab = True


class QuantityPriceBreakInline(TabularInline):
    model = QuantityPriceBreak
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("product", "min_qty", "discount_pct", "price", "note")
    verbose_name_plural = "پله‌های قیمت حجمی"
    tab = True


class PriceListItemResource(resources.ModelResource):
    """ورود/خروج اکسل قیمت‌ها (به‌روزرسانی گروهی قیمت کاتالوگ)."""

    class Meta:
        model = PriceListItem
        fields = ("id", "price_list__code", "product__code", "price", "valid_from", "valid_until", "note")
        import_id_fields = ("price_list__code", "product__code")
        skip_unchanged = True


@admin.register(PriceList)
class PriceListAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "code", "kind_badge", "discount_pct", "company_count", "item_count",
                    "validity_col", "status_badge", "is_active")
    list_filter = (("kind", ChoicesDropdownFilter), "is_active")
    search_fields = ("name", "code", "note")
    readonly_fields = ("created_at",)
    inlines = [PriceListItemInline, QuantityPriceBreakInline]
    actions = ["action_extend_30", "action_deactivate"]
    fieldsets = (
        ("سبد قیمت", {"fields": ("name", "code", "kind", "discount_pct")}),
        ("اعتبار", {"fields": ("valid_from", "valid_until", "is_active", "note")}),
    )

    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        color = {"list": "#64748b", "partner": "#0e7490", "project": "#6d28d9",
                 "contractor": "#1d4ed8", "export": "#b45309", "internal": "#0891b2"}.get(obj.kind)
        return badge(obj.get_kind_display(), color=color)

    @admin.display(description="مشتریان")
    def company_count(self, obj):
        return badge(f"{num(obj.companies.count())} شرکت", key="primary")

    @admin.display(description="اقلام")
    def item_count(self, obj):
        return num(obj.items.count())

    @admin.display(description="اعتبار")
    def validity_col(self, obj):
        if not obj.valid_until:
            return "بدون انقضا"
        return format_html("{} تا {}", jalali(obj.valid_from) if obj.valid_from else "—",
                           jalali(obj.valid_until))

    @admin.display(description="وضعیت")
    def status_badge(self, obj):
        label, color = obj.status_label
        return badge(label, color=color)

    @admin.action(description="تمدید اعتبار ۳۰ روز")
    def action_extend_30(self, request, queryset):
        count = 0
        for price_list in queryset:
            base = price_list.valid_until or timezone.localdate()
            price_list.valid_until = base + timezone.timedelta(days=30)
            price_list.save(update_fields=["valid_until"])
            count += 1
        self.message_user(request, f"اعتبار {num(count)} سبد قیمت ۳۰ روز تمدید شد.", messages.SUCCESS)

    @admin.action(description="غیرفعال‌سازی سبد قیمت")
    def action_deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(PriceListItem)
class PriceListItemAdmin(ModelHelpMixin, ImportExportModelAdmin, ModelAdmin):
    resource_class = PriceListItemResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    compressed_fields = True
    list_per_page = 30

    list_display = ("price_list", "product", "price_col", "base_price_col", "diff_col",
                    "validity_col", "note")
    list_filter = (("price_list", RelatedDropdownFilter),
                   ("product__category", RelatedDropdownFilter),
                   ("price_list__kind", ChoicesDropdownFilter))
    search_fields = ("product__code", "product__name", "price_list__name")
    autocomplete_fields = ("price_list", "product")
    actions = ["action_apply_discount_5", "action_clear_expiry"]

    @admin.display(description="قیمت سبد", ordering="price")
    def price_col(self, obj):
        return money_compact(obj.price)

    @admin.display(description="قیمت پایه")
    def base_price_col(self, obj):
        return money_compact(obj.product.base_price)

    @admin.display(description="اختلاف")
    def diff_col(self, obj):
        base = obj.product.base_price or 0
        if not base:
            return "—"
        pct = round((base - obj.price) * 100 / base, 1)
        return badge(f"{num(pct, 1)}٪ تخفیف", key="ok" if pct > 0 else "muted")

    @admin.display(description="اعتبار")
    def validity_col(self, obj):
        if not (obj.valid_from or obj.valid_until):
            return "—"
        return format_html("{} ← {}", jalali(obj.valid_from) if obj.valid_from else "—",
                           jalali(obj.valid_until) if obj.valid_until else "—")

    @admin.action(description="اعمال تخفیف ۵٪ روی اقلام انتخابی")
    def action_apply_discount_5(self, request, queryset):
        count = 0
        for item in queryset:
            item.price = int(round(item.price * 0.95))
            item.save(update_fields=["price"])
            count += 1
        self.message_user(request, f"قیمت {num(count)} قلم ۵٪ کاهش یافت.", messages.SUCCESS)

    @admin.action(description="حذف تاریخ انقضای اقلام انتخابی")
    def action_clear_expiry(self, request, queryset):
        queryset.update(valid_until=None)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("price_list", "product")


@admin.register(QuantityPriceBreak)
class QuantityPriceBreakAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("product", "price_list", "min_qty", "discount_pct", "price_col",
                    "computed_price_col", "note")
    list_filter = (("price_list", RelatedDropdownFilter),
                   ("product__category", RelatedDropdownFilter))
    search_fields = ("product__code", "product__name", "price_list__name")
    autocomplete_fields = ("price_list", "product")
    actions = ["action_asymmetric_check"]

    @admin.display(description="قیمت واحد")
    def price_col(self, obj):
        return money_compact(obj.price) if obj.price else badge("محاسبه از درصد", key="muted")

    @admin.display(description="قیمت محاسبه‌شده")
    def computed_price_col(self, obj):
        return money_compact(obj.unit_price(obj.product.base_price))

    @admin.action(description="بررسی منطقی بودن پله‌ها")
    def action_asymmetric_check(self, request, queryset):
        problems = []
        for product_id in queryset.values_list("product_id", flat=True).distinct():
            breaks = list(QuantityPriceBreak.objects.filter(product_id=product_id).order_by("min_qty"))
            for previous, current in zip(breaks, breaks[1:]):
                if current.unit_price(current.product.base_price) > previous.unit_price(previous.product.base_price):
                    problems.append(f"{current.product.code} (پله {current.min_qty}+ گران‌تر از پله قبل)")
        if problems:
            self.message_user(request, "پله‌های غیرمنطقی: " + "، ".join(problems[:5]), messages.WARNING)
        else:
            self.message_user(request, "همه‌ی پله‌های بررسی‌شده منطقی هستند (قیمت با افزایش تعداد کاهش می‌یابد).",
                              messages.SUCCESS)
