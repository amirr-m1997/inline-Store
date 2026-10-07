"""ادمین کاتالوگ: محصول فنی، دسته‌بندی، برند، قالب مشخصات، اسناد، روابط."""
from __future__ import annotations

from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.admin_utils import ModelHelpMixin, COLORS, PanelModelAdmin, badge, html_table, money_compact, progress_bar
from core.utils import jalali, num

from .models import Brand, Category, Product, ProductDocument, ProductImage, ProductRelation, SpecTemplate

# --------------------------------------------------------------- Inlines


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt", "is_main", "order")
    tab = True


class ProductDocumentInline(TabularInline):
    model = ProductDocument
    extra = 0
    fields = ("kind", "title", "version", "is_latest", "file", "reviewed_at", "approved_by")
    tab = True


class ProductRelationInline(TabularInline):
    model = ProductRelation
    fk_name = "product"
    extra = 0
    autocomplete_fields = ("target",)
    fields = ("kind", "target", "note")
    verbose_name_plural = "سازگاری، لوازم جانبی و جایگزین"
    tab = True


class StockItemInline(TabularInline):
    from inventory.models import StockItem as _StockItem

    model = _StockItem
    extra = 0
    can_delete = False
    fields = ("warehouse", "on_hand", "reserved", "incoming", "min_level", "reorder_point")
    readonly_fields = ("warehouse",)
    verbose_name_plural = "موجودی در انبارها"
    tab = True


# --------------------------------------------------------------- Resources


class ProductResource(resources.ModelResource):
    """ورود/خروج اکسل محصولات صنعتی (مطابق ستون‌های کاتالوگ)."""

    specs_json = Field(attribute="specs", column_name="مشخصات فنی (JSON)")

    class Meta:
        model = Product
        fields = (
            "id", "code", "name", "name_en", "model_number", "category__name", "brand__name",
            "base_price", "uom", "min_order_qty", "max_order_qty", "packaging_multiple",
            "lead_time_days", "availability", "unspsc_code", "hs_code", "dimensions",
            "weight_kg", "origin_country", "warranty_months", "tags", "is_active", "specs_json",
        )
        export_order = fields
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True


# --------------------------------------------------------------- Admins


@admin.register(Category)
class CategoryAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "parent", "code", "product_count", "is_featured", "order", "is_active")
    list_filter = ("is_featured", "is_active", ("parent", RelatedDropdownFilter))
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)

    @admin.display(description="تعداد محصول")
    def product_count(self, obj):
        count = getattr(obj, "products_count", None) or obj.products.count()
        return badge(f"{num(count)} قلم", key="primary" if count else "muted")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count("products"))


@admin.register(Brand)
class BrandAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "name_en", "country", "is_internal_engine_brand", "product_count", "is_active")
    list_filter = ("is_internal_engine_brand", "is_active")
    search_fields = ("name", "name_en")

    @admin.display(description="تعداد محصول")
    def product_count(self, obj):
        return badge(f"{num(obj.products.count())} قلم", key="primary")


@admin.register(SpecTemplate)
class SpecTemplateAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("name", "category", "field_count", "is_active", "note")
    list_filter = (("category", RelatedDropdownFilter), "is_active")
    search_fields = ("name",)
    readonly_fields = ("spec_fields_preview",)
    fieldsets = (
        ("قالب", {"fields": ("name", "category", "is_active", "note")}),
        ("فیلدهای مشخصات", {
            "fields": ("fields", "spec_fields_preview"),
            "description": "ساختار هر فیلد: {\"key\": \"capacity\", \"label\": \"ظرفیت سرمایش\", "
                           "\"unit\": \"TR\", \"type\": \"number\"}",
        }),
    )

    @admin.display(description="پیش‌نمایش فیلدها")
    def spec_fields_preview(self, obj):
        rows = [
            [f.get("label", "—"), f.get("key", "—"), f.get("unit", "—"), f.get("type", "text")]
            for f in (obj.fields or [])
        ]
        return html_table(["عنوان", "کلید", "واحد", "نوع"], rows) if rows else "فیلدی ثبت نشده است."


@admin.register(Product)
class ProductAdmin(ModelHelpMixin, ImportExportModelAdmin, ModelAdmin):
    resource_class = ProductResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_fullwidth = True
    list_per_page = 30
    save_on_top = True
    empty_value_display = "—"

    list_display = (
        "code", "name", "category", "brand", "price_col", "availability_badge",
        "stock_badge", "sales_rules", "lead_time_col", "is_active",
    )
    list_display_links = ("code", "name")
    list_filter = (
        ("availability", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("brand", RelatedDropdownFilter),
        ("uom", ChoicesDropdownFilter),
        "is_active", "is_featured",
    )
    search_fields = ("code", "name", "name_en", "model_number", "tags", "unspsc_code")
    autocomplete_fields = ("category", "brand", "spec_template", "substitute")
    readonly_fields = ("stock_summary", "price_levels_table", "spec_table", "created_at", "updated_at")
    inlines = [ProductDocumentInline, StockItemInline, ProductRelationInline, ProductImageInline]
    actions = ["action_clearance", "action_featured_on", "action_featured_off", "action_discontinue"]

    fieldsets = (
        ("شناسه کالا", {
            "fields": (("code", "model_number"), ("name", "name_en"), ("category", "brand"),
                       ("spec_template", "substitute")),
        }),
        ("قیمت و قواعد فروش", {
            "fields": (("base_price", "uom", "alt_uom", "uom_factor"),
                       ("min_order_qty", "max_order_qty", "packaging_multiple"),
                       ("lead_time_days", "warranty_months")),
            "description": "قیمت پایه، قیمت لیست است؛ قیمت هر مشتری را سبد قیمت و پله‌های حجمی تعیین می‌کند.",
        }),
        ("وضعیت و انبار", {"fields": ("availability", "is_active", "is_featured", "stock_summary")}),
        ("مشخصات فنی", {"fields": ("specs", "spec_table")}),
        ("توضیحات و شناسه‌های استاندارد", {
            "fields": ("short_description", "description", "tags",
                       ("weight_kg", "dimensions"), ("origin_country", "unspsc_code", "hs_code")),
        }),
        ("قیمت‌های پلکانی و سبدها", {"fields": ("price_levels_table",)}),
        ("ردیابی", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # -------------------------------------------------- ستون‌های لیست
    @admin.display(description="قیمت پایه", ordering="base_price")
    def price_col(self, obj):
        return money_compact(obj.base_price)

    @admin.display(description="وضعیت کالا")
    def availability_badge(self, obj):
        return badge(obj.get_availability_display(), color=obj.availability_color)

    @admin.display(description="موجودی")
    def stock_badge(self, obj):
        _, label, color = obj.stock_status
        free = obj.free_qty
        return badge(f"{label} ({num(free, 0)})", color=color)

    @admin.display(description="MOQ / بسته")
    def sales_rules(self, obj):
        return format_html(
            '<span style="font-size:11.5px;color:var(--panel-text-muted)">MOQ {} / مضرب {}</span>',
            num(obj.min_order_qty, 0), num(obj.packaging_multiple, 0),
        )

    @admin.display(description="زمان تأمین", ordering="lead_time_days")
    def lead_time_col(self, obj):
        days = obj.lead_time_days
        if not days:
            return badge("تحویل فوری", key="ok")
        key = "warn" if days > 30 else "primary"
        return badge(f"{num(days)} روز", key=key)

    # -------------------------------------------------- فیلدهای readonly
    @admin.display(description="خلاصه موجودی و کدها")
    def stock_summary(self, obj):
        if not obj.pk:
            return "—"
        rows = [
            [item.warehouse.name, num(item.on_hand, 0), num(item.reserved, 0),
             num(item.free_qty, 0), num(item.reorder_point, 0), item.status[1]]
            for item in obj.stock_items.select_related("warehouse")
        ]
        table = html_table(["انبار", "موجودی", "رزرو", "آزاد (ATP)", "نقطه سفارش", "وضعیت"], rows,
                           "موجودی به تفکیک انبار")
        links = format_html(
            '<div style="margin-top:10px">{}{}</div>',
            format_html('<a class="text-primary" href="{}">ویرایش موجودی‌ها</a>',
                        reverse("admin:inventory_stockitem_changelist") + f"?product__id__exact={obj.pk}"),
            "",
        )
        return format_html("{}{}", table, links)

    @admin.display(description="مشخصات فنی ساختاریافته")
    def spec_table(self, obj):
        if not obj.specs:
            return "مشخصات فنی ثبت نشده است."
        labels = {}
        if obj.spec_template:
            labels = {f.get("key"): f for f in (obj.spec_template.fields or [])}
        rows = []
        for key, value in (obj.specs or {}).items():
            meta = labels.get(key, {})
            label = meta.get("label", key)
            unit = meta.get("unit", "")
            display = "بله" if value is True else ("خیر" if value is False else value)
            rows.append([label, f"{display} {unit}".strip()])
        return html_table(["ویژگی", "مقدار"], rows, f"قالب: {obj.spec_template.name if obj.spec_template else '—'}")

    @admin.display(description="پله‌های قیمت برای نمونه مشتری")
    def price_levels_table(self, obj):
        if not obj.pk:
            return "ابتدا کالا را ذخیره کنید."
        from pricing.services import price_levels_for

        company = obj.price_items.first().price_list.companies.first() if obj.price_items.exists() else None
        rows = [
            [num(row["qty"], 0), num(row["unit_price"], 0), f"{num(row['discount_pct'], 2)}٪",
             row["source"]]
            for row in price_levels_for(obj, company=company)
        ]
        note = format_html(
            '<div style="margin-top:8px;font-size:11.5px;color:var(--panel-text-muted)">'
            'نمونه بر اساس سبد قیمت مشتری «{}»</div>',
            company.name if company else "بدون سبد اختصاصی (قیمت پایه)",
        )
        return format_html("{}{}", html_table(["تعداد", "قیمت واحد", "تخفیف", "منبع قیمت"], rows),
                           note)

    # -------------------------------------------------- اکشن‌ها
    @admin.action(description="علامت‌گذاری به‌عنوان متوقف تولید")
    def action_discontinue(self, request, queryset):
        updated = queryset.update(availability="discontinued")
        self.message_user(request, f"{num(updated)} کالا متوقف‌شده علامت خورد.", messages.SUCCESS)

    @admin.action(description="افزودن به کالاهای ویژه")
    def action_featured_on(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="حذف از کالاهای ویژه")
    def action_featured_off(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description="بررسی فنی و پاکسازی قیمت صفر")
    def action_clearance(self, request, queryset):
        zero_price = queryset.filter(base_price=0).count()
        self.message_user(
            request,
            f"{num(queryset.count())} کالا بررسی شد؛ {num(zero_price)} کالا قیمت پایه صفر دارد.",
            messages.WARNING if zero_price else messages.SUCCESS,
        )

    # -------------------------------------------------- دسترسی‌ها
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("category", "brand", "spec_template")
            .prefetch_related("stock_items", "price_items__price_list")
        )


@admin.register(ProductDocument)
class ProductDocumentAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("product",)
    list_display = ("product", "kind_badge", "title", "version", "is_latest",
                    "reviewed_col", "approved_by", "file_link")
    list_filter = (("kind", ChoicesDropdownFilter), "is_latest",
                   ("product__category", RelatedDropdownFilter))
    search_fields = ("title", "product__code", "product__name", "approved_by")
    autocomplete_fields = ("product",)
    actions = ["action_approve_technical"]
    fieldsets = (
        ("سند", {"fields": ("product", "kind", "title")}),
        ("فایل", {"fields": ("file", "external_url")}),
        ("نسخه و تأیید", {"fields": ("version", "is_latest", "reviewed_at", "approved_by", "note")}),
    )

    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        return badge(obj.get_kind_display(), color=obj.kind_color)

    @admin.display(description="آخرین بازبینی", ordering="reviewed_at")
    def reviewed_col(self, obj):
        return jalali(obj.reviewed_at) if obj.reviewed_at else "—"

    @admin.display(description="فایل")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">دانلود</a>', obj.file.url)
        if obj.external_url:
            return format_html('<a href="{}" target="_blank">لینک</a>', obj.external_url)
        return "—"

    @admin.action(description="تأیید فنی و ثبت به‌عنوان آخرین نسخه")
    def action_approve_technical(self, request, queryset):
        count = 0
        for document in queryset:
            ProductDocument.objects.filter(product=document.product, kind=document.kind).update(
                is_latest=False)
            document.is_latest = True
            document.reviewed_at = timezone.localdate()
            document.approved_by = request.user.get_full_name() or request.user.username
            document.save(update_fields=["is_latest", "reviewed_at", "approved_by"])
            count += 1
        self.message_user(request, f"{num(count)} سند تأیید فنی و به‌عنوان آخرین نسخه ثبت شد.",
                          messages.SUCCESS)


@admin.register(ProductRelation)
class ProductRelationAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("product", "kind_badge", "target", "note")
    list_filter = (("kind", ChoicesDropdownFilter),)
    search_fields = ("product__code", "product__name", "target__code", "target__name")
    autocomplete_fields = ("product", "target")

    @admin.display(description="نوع رابطه", ordering="kind")
    def kind_badge(self, obj):
        color = {"compatible": COLORS["primary"], "accessory": COLORS["info"],
                 "substitute": COLORS["warn"], "complement": COLORS["violet"]}.get(obj.kind)
        return badge(obj.get_kind_display(), color=color)


@admin.register(ProductImage)
class ProductImageAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("product", "alt", "is_main", "order")
    list_filter = ("is_main",)
    search_fields = ("product__code", "product__name", "alt")
    autocomplete_fields = ("product",)
