from datetime import timedelta
from django.utils import timezone
from django.db.models import F
from apps.common.jalali import format_jalali
from .export_services import clean_html_description, estimate_pages_and_stats, export_products_to_excel_response
from django import forms
from django.contrib import admin
from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from apps.inventory.models import Inventory, ReplenishmentRule
from apps.pricing.models import ProductPrice
from .admin_widgets import CategoryPickerWidget
from .models import AttributeDefinition, Category, CategoryAttribute, CategorySlugRedirect, Product, ProductAttributeValue, ProductBrand, ProductDocument, ProductFavorite, ProductIdentifier, ProductImage, ProductQuestion, ProductReview, SupplyBrand

def category_path(category):
    """Return a compact, unambiguous admin label for a catalog category."""
    parts = []
    current = category
    while current is not None:
        parts.append(current.name_fa)
        current = current.parent
    return " / ".join(reversed(parts))


class HierarchicalCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{category_path(obj)} ({obj.code})"


class HierarchicalCategoryAdminMixin:
    """Make category foreign-key selectors understandable without changing data."""

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.remote_field.model is Category:
            kwargs["queryset"] = Category.objects.select_related("parent").order_by("level", "parent_id", "code")
            kwargs["form_class"] = HierarchicalCategoryChoiceField
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_fa", "alt_en", "is_primary", "sort_order")
class InventoryInline(admin.StackedInline): model = Inventory; extra = 0; max_num = 1
class ReplenishmentRuleInline(admin.StackedInline):
    model = ReplenishmentRule
    extra = 0
    max_num = 1
    fields = ("minimum_quantity", "maximum_quantity", "order_multiple", "lead_time_days", "is_auto", "is_active")
class ProductPriceInline(admin.TabularInline): model = ProductPrice; extra = 0
class ProductIdentifierInline(admin.TabularInline): model = ProductIdentifier; extra = 0
class ProductAttributeValueInline(admin.TabularInline): model = ProductAttributeValue; extra = 0; autocomplete_fields = ("attribute",)
class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 0
    fields = ("document_type", "title_fa", "title_en", "file", "display_name", "language", "revision", "display_order", "is_active", "is_published")

    def get_formset(self, request, obj=None, **kwargs):
        """Make the file field optional when editing an existing document.
        For existing instances where a file is already present, the admin form
        should not require re‑uploading the file. This method adjusts the formset
        accordingly and ensures validation does not fail on unchanged files.
        """
        FormSet = super().get_formset(request, obj, **kwargs)
        if obj:
            # Make file optional for the inline form.
            if "file" in FormSet.form.base_fields:
                FormSet.form.base_fields["file"].required = False
            # Patch save_existing to skip file validation when unchanged.
            orig_save_existing = FormSet.save_existing
            def save_existing(self, form, instance, commit=True):
                if not form.cleaned_data.get("file"):
                    instance.full_clean(exclude=["file"])
                else:
                    instance.full_clean()
                return orig_save_existing(form, instance, commit)
            FormSet.save_existing = save_existing.__get__(FormSet, FormSet.__class__)
        return FormSet
class CategoryAttributeInline(admin.TabularInline): model = CategoryAttribute; extra = 0; autocomplete_fields = ("attribute",)
class ProductReviewInline(admin.TabularInline): model = ProductReview; extra = 0; fields = ("user", "rating", "comment", "is_published", "updated_at"); readonly_fields = ("user", "rating", "comment", "updated_at"); can_delete = False
class ProductQuestionInline(admin.TabularInline): model = ProductQuestion; extra = 0; fields = ("user", "question", "answer", "is_published", "updated_at"); readonly_fields = ("user", "question", "updated_at")
@admin.register(Category)
class CategoryAdmin(HierarchicalCategoryAdminMixin, admin.ModelAdmin):
    list_display = ("tree_name", "code", "slug", "parent_path", "level", "is_active")
    list_filter = ("is_active", "level")
    search_fields = ("name_fa", "name_en", "code", "slug", "parent__name_fa")
    ordering = ("level", "parent_id", "code")
    inlines = (CategoryAttributeInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent", "parent__parent")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("picker/", self.admin_site.admin_view(self.picker_view), name="catalog_category_picker"),
            path("browse/", self.admin_site.admin_view(self.browse_view), name="catalog_category_browse"),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Make the Categories menu open the level-by-level browser, not the flat table."""
        return HttpResponseRedirect(reverse("admin:catalog_category_browse"))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        parent_field = form.base_fields.get("parent")
        if parent_field is not None:
            excluded_ids = obj.descendant_ids() if obj is not None else ()
            parent_field.widget = CategoryPickerWidget(
                picker_url=reverse("admin:catalog_category_picker"),
                allow_empty=True,
                exclude_ids=excluded_ids,
            )
        return form

    def picker_view(self, request):
        """JSON data for the shared, step-by-step category selector widget."""
        excluded_ids = set()
        for value in request.GET.get("exclude", "").split(","):
            if value.isdigit():
                excluded_ids.add(int(value))
        query = request.GET.get("q", "").strip()
        parent_id = request.GET.get("parent")
        child_exists = Category.objects.filter(parent=OuterRef("pk"))
        categories = Category.objects.exclude(pk__in=excluded_ids).annotate(has_children=Exists(child_exists))
        if query:
            categories = categories.filter(Q(name_fa__icontains=query) | Q(name_en__icontains=query) | Q(code__icontains=query))
        elif parent_id and parent_id.isdigit():
            categories = categories.filter(parent_id=int(parent_id))
        elif not parent_id:
            categories = categories.filter(parent__isnull=True)
        else:
            categories = categories.none()
        results = [
            {"id": category.pk, "name": category.name_fa, "code": category.code, "has_children": category.has_children}
            for category in categories.order_by("code", "name_fa", "id")[:100]
        ]
        return JsonResponse({"results": results})
    def browse_view(self, request):
        parent_id = request.GET.get("parent")
        parent = None
        if parent_id:
            parent = get_object_or_404(Category.objects.select_related("parent", "parent__parent"), pk=parent_id)
        child_exists = Category.objects.filter(parent=OuterRef("pk"))
        children = (
            Category.objects.filter(parent=parent)
            .annotate(has_children=Exists(child_exists))
            .order_by("code", "name_fa", "id")
        )
        ancestors = []
        cursor = parent
        while cursor is not None:
            ancestors.append(cursor)
            cursor = cursor.parent
        ancestors.reverse()
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "مرور دسته‌بندی‌ها",
            "current_parent": parent,
            "children": children,
            "ancestors": ancestors,
        }
        return TemplateResponse(request, "admin/catalog/category/browse.html", context)

    @admin.display(description="دسته‌بندی", ordering="name_fa")
    def tree_name(self, obj):
        marker = "└─ " if obj.level else "● "
        return format_html('<span style="padding-right: {}em">{}{}</span>', obj.level * 1.5, marker, obj.name_fa)

    @admin.display(description="مسیر والد", ordering="parent__name_fa")
    def parent_path(self, obj):
        return category_path(obj.parent) if obj.parent_id else "دسته اصلی"
@admin.register(CategorySlugRedirect)
class CategorySlugRedirectAdmin(admin.ModelAdmin):
    list_display = ("old_slug", "category"); search_fields = ("old_slug", "category__name_fa", "category__slug")


class RecentlyCreatedListFilter(admin.SimpleListFilter):
    title = "زمان ثبت (محصولات جدید)"
    parameter_name = "recently_created"

    def lookups(self, request, model_admin):
        return (
            ("today", "ثبت شده امروز"),
            ("24h", "۲۴ ساعت اخیر"),
            ("7d", "۷ روز گذشته"),
            ("30d", "۳۰ روز گذشته"),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        val = self.value()
        if val == "today":
            start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_of_today)
        if val == "24h":
            return queryset.filter(created_at__gte=now - timedelta(days=1))
        if val == "7d":
            return queryset.filter(created_at__gte=now - timedelta(days=7))
        if val == "30d":
            return queryset.filter(created_at__gte=now - timedelta(days=30))
        return queryset


class RecentlyUpdatedListFilter(admin.SimpleListFilter):
    title = "زمان ویرایش (به‌روزرسانی اخیر)"
    parameter_name = "recently_updated"

    def lookups(self, request, model_admin):
        return (
            ("today", "ویرایش شده امروز"),
            ("24h", "۲۴ ساعت اخیر"),
            ("7d", "۷ روز گذشته"),
            ("30d", "۳۰ روز گذشته"),
            ("modified_only", "فقط تغییریافته پس از ثبت"),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        val = self.value()
        if val == "today":
            start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(updated_at__gte=start_of_today)
        if val == "24h":
            return queryset.filter(updated_at__gte=now - timedelta(days=1))
        if val == "7d":
            return queryset.filter(updated_at__gte=now - timedelta(days=7))
        if val == "30d":
            return queryset.filter(updated_at__gte=now - timedelta(days=30))
        if val == "modified_only":
            return queryset.filter(updated_at__gt=F("created_at") + timedelta(seconds=60))
        return queryset

@admin.register(Product)
class ProductAdmin(HierarchicalCategoryAdminMixin, admin.ModelAdmin):
    list_display = (
        "code",
        "product_name_link",
        "brand",
        "category",
        "unit",
        "created_at_display",
        "updated_at_display",
        "description_status",
        "is_featured",
        "is_obsolete",
        "is_active",
    )
    list_filter = (
        RecentlyCreatedListFilter,
        RecentlyUpdatedListFilter,
        "is_featured",
        "is_obsolete",
        "is_active",
        "brand",
        "category",
    )
    search_fields = ("code", "name", "slug", "identifiers__normalized_value", "documents__display_name")
    ordering = ("-updated_at", "-id")
    date_hierarchy = "updated_at"
    inlines = (
        ProductImageInline,
        ProductDocumentInline,
        InventoryInline,
        ReplenishmentRuleInline,
        ProductPriceInline,
        ProductIdentifierInline,
        ProductAttributeValueInline,
        ProductReviewInline,
        ProductQuestionInline,
    )
    list_editable = ("is_featured", "is_obsolete")
    autocomplete_fields = ("brand", "replacement_product")
    actions = ("export_selected_to_excel",)
    list_display_links = ("code",)
    view_on_site = True

    fieldsets = (
        ("اطلاعات شناسنامه‌ای و دسته‌بندی محصول", {
            "fields": (
                ("code", "name"),
                ("slug", "category"),
                ("brand", "unit", "condition"),
            )
        }),
        ("وضعیت انتشار و کاتالوگ", {
            "fields": (
                ("is_active", "is_featured", "is_obsolete"),
                "replacement_product",
            )
        }),
        ("توضیحات و مستندات فنی محصول (پشتیبانی از متن‌های چند صفحه‌ای)", {
            "fields": ("description", "technical_specs"),
            "description": "توضیحات جامع محصول. برای ویرایش راحت متون چند صفحه‌ای، می‌توانید از دکمه Maximize (تمام‌صفحه) در نوار ابزار ادیتور استفاده نمایید.",
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("export-excel/", self.admin_site.admin_view(self.export_excel_view), name="catalog_product_export_excel"),
            path("<int:product_id>/preview-description/", self.admin_site.admin_view(self.preview_description_view), name="catalog_product_preview_description"),
        ]
        return custom_urls + urls

    @admin.action(description="تهیه نسخه پشتیبان اکسل از محصولات انتخاب‌شده (Backup XLSX)")
    def export_selected_to_excel(self, request, queryset):
        return export_products_to_excel_response(queryset, filename_prefix="backup_selected_products")

    def export_excel_view(self, request):
        """
        Export products to Excel based on current active filters, search queries, or date range.
        """
        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)

        recently_created = request.GET.get("recently_created")
        recently_updated = request.GET.get("recently_updated")
        if recently_created:
            prefix = f"backup_new_products_{recently_created}"
        elif recently_updated:
            prefix = f"backup_updated_products_{recently_updated}"
        else:
            prefix = "backup_products"

        return export_products_to_excel_response(queryset, filename_prefix=prefix)

    def preview_description_view(self, request, product_id):
        product = get_object_or_404(Product.objects.select_related("category", "brand"), pk=product_id)
        clean_text = clean_html_description(product.description)
        pages, words, chars, label = estimate_pages_and_stats(clean_text)
        context = {
            **self.admin_site.each_context(request),
            "title": f"پیش‌نمایش توضیحات: {product.name}",
            "product": product,
            "clean_text": clean_text,
            "raw_html": product.description or "",
            "pages": pages,
            "words": words,
            "chars": chars,
            "pages_label": label,
        }
        return TemplateResponse(request, "admin/catalog/product/preview_description.html", context)

    @admin.display(description="نام محصول (مشاهده در کلاینت ↗)", ordering="name")
    def product_name_link(self, obj):
        url = obj.get_absolute_url()
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer" style="font-weight: 600; color: #0d5c63; text-decoration: none;" title="مشاهده زنده در کلاینت">'
            '{} <span style="font-size: 11px; opacity: 0.8; vertical-align: middle;">↗</span></a>',
            url,
            obj.name,
        )

    @admin.display(description="تاریخ ثبت", ordering="created_at")
    def created_at_display(self, obj):
        return format_jalali(obj.created_at, with_time=False)

    @admin.display(description="آخرین ویرایش", ordering="updated_at")
    def updated_at_display(self, obj):
        return format_jalali(obj.updated_at, with_time=True)

    @admin.display(description="توضیحات و حجم")
    def description_status(self, obj):
        clean = clean_html_description(obj.description)
        if not clean:
            return format_html('<span style="color: #94a3b8; font-size: 11px;">فاقد توضیحات</span>')
        pages, words, chars, label = estimate_pages_and_stats(clean)
        preview_url = reverse("admin:catalog_product_preview_description", args=[obj.pk])
        if pages > 1:
            badge = format_html(
                '<span style="background: #fef3c7; color: #92400e; padding: 2px 7px; border-radius: 6px; font-weight: 600; font-size: 11px;">📄 {}</span>',
                label
            )
        else:
            badge = format_html(
                '<span style="background: #e0f2fe; color: #0369a1; padding: 2px 7px; border-radius: 6px; font-size: 11px;">📝 {}</span>',
                label
            )
        return format_html(
            '{} <a href="{}" onclick="window.open(this.href, \'_blank\', \'width=750,height=600,scrollbars=yes\'); return false;" title="مشاهده پیش‌نمایش توضیحات" style="margin-right: 4px; text-decoration: none; font-size: 13px;">👁️</a>',
            badge,
            preview_url
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj=obj, change=change, **kwargs)
        category_field = form.base_fields.get("category")
        if category_field is not None:
            category_field.widget = CategoryPickerWidget(
                picker_url=reverse("admin:catalog_category_picker"),
            )
        description_field = form.base_fields.get("description")
        if description_field is not None:
            from ckeditor.widgets import CKEditorWidget
            description_field.widget = CKEditorWidget(config_name="default")
        return form
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin): list_display = ("product", "is_primary", "sort_order"); list_filter = ("is_primary",); search_fields = ("product__code", "alt_text", "alt_fa", "alt_en")
@admin.register(ProductFavorite)
class ProductFavoriteAdmin(admin.ModelAdmin): list_display = ("product", "user", "created_at"); search_fields = ("product__code", "product__name", "user__username"); autocomplete_fields = ("product", "user")
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin): list_display = ("product", "user", "rating", "is_published", "updated_at"); list_filter = ("rating", "is_published"); list_editable = ("is_published",); search_fields = ("product__code", "product__name", "user__username", "comment"); autocomplete_fields = ("product", "user")
@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "short_question", "is_published", "updated_at")
    list_filter = ("is_published",)
    list_editable = ("is_published",)
    search_fields = ("product__code", "product__name", "user__username", "question", "answer")
    autocomplete_fields = ("product", "user")

    @admin.display(description="پرسش")
    def short_question(self, obj): return obj.question[:70]
@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ("display_name", "product", "document_type", "language", "revision", "file_size", "is_active", "is_published", "updated_at", "display_order")
    list_filter = ("document_type", "language", "is_active", "is_published")
    search_fields = ("display_name", "title_fa", "title_en", "revision", "product__code", "product__name")
    ordering = ("product__code", "display_order", "id")
    autocomplete_fields = ("product",)
@admin.register(SupplyBrand)
class SupplyBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active"); list_editable = ("order", "is_active"); search_fields = ("name",); ordering = ("order", "name")
@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "slug", "is_active", "is_published"); list_filter = ("is_active", "is_published"); search_fields = ("name", "code", "slug"); prepopulated_fields = {"slug": ("name",)}
@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "code", "value_type", "unit", "is_filterable", "is_comparable", "is_active"); list_filter = ("value_type", "is_filterable", "is_comparable", "is_active"); search_fields = ("name_fa", "name_en", "code"); ordering = ("display_order", "name_fa")
@admin.register(ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ("display_value", "identifier_type", "product"); list_filter = ("identifier_type",); search_fields = ("normalized_value", "display_value", "product__code", "product__name"); autocomplete_fields = ("product",)
@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("product", "attribute", "text_value", "number_value", "boolean_value", "enum_value"); list_filter = ("attribute",); search_fields = ("product__code", "product__name", "enum_value", "text_value"); autocomplete_fields = ("product", "attribute")
@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(HierarchicalCategoryAdminMixin, admin.ModelAdmin):
    list_display = ("category", "attribute", "is_required", "is_filterable", "unit_override", "display_order")
    list_filter = ("is_required", "is_filterable")
    search_fields = ("category__name_fa", "category__code", "attribute__name_fa", "attribute__code")
    autocomplete_fields = ("category", "attribute")
    ordering = ("category", "display_order", "attribute__name_fa")
