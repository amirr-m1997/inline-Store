from django.contrib import admin
from django import forms
from django.utils.html import format_html
from apps.inventory.models import Inventory
from apps.pricing.models import ProductPrice
from .models import AttributeDefinition, Category, CategoryAttribute, CategorySlugRedirect, Product, ProductAttributeValue, ProductBrand, ProductDocument, ProductIdentifier, ProductImage, SupplyBrand


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
class ProductPriceInline(admin.TabularInline): model = ProductPrice; extra = 0
class ProductIdentifierInline(admin.TabularInline): model = ProductIdentifier; extra = 0
class ProductAttributeValueInline(admin.TabularInline): model = ProductAttributeValue; extra = 0; autocomplete_fields = ("attribute",)
class ProductDocumentInline(admin.TabularInline): model = ProductDocument; extra = 0; fields = ("document_type", "title_fa", "title_en", "file", "display_name", "language", "revision", "display_order", "is_active", "is_published")
class CategoryAttributeInline(admin.TabularInline): model = CategoryAttribute; extra = 0; autocomplete_fields = ("attribute",)
@admin.register(Category)
class CategoryAdmin(HierarchicalCategoryAdminMixin, admin.ModelAdmin):
    list_display = ("tree_name", "code", "slug", "parent_path", "level", "is_active")
    list_filter = ("is_active", "level")
    search_fields = ("name_fa", "name_en", "code", "slug", "parent__name_fa")
    ordering = ("level", "parent_id", "code")
    inlines = (CategoryAttributeInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent", "parent__parent")

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
@admin.register(Product)
class ProductAdmin(HierarchicalCategoryAdminMixin, admin.ModelAdmin):
    list_display = ("code", "name", "brand", "category", "unit", "is_featured", "is_active"); list_filter = ("is_featured", "is_active", "brand", "category"); search_fields = ("code", "name", "slug", "identifiers__normalized_value", "documents__display_name"); ordering = ("code",); inlines = (ProductImageInline, ProductDocumentInline, InventoryInline, ProductPriceInline, ProductIdentifierInline, ProductAttributeValueInline); list_editable = ("is_featured",); autocomplete_fields = ("brand",)
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin): list_display = ("product", "is_primary", "sort_order"); list_filter = ("is_primary",); search_fields = ("product__code", "alt_text", "alt_fa", "alt_en")
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
