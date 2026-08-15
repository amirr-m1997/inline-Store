from django.contrib import admin
from apps.inventory.models import Inventory
from apps.pricing.models import ProductPrice
from .models import AttributeDefinition, Category, CategoryAttribute, CategorySlugRedirect, Product, ProductAttributeValue, ProductBrand, ProductDocument, ProductIdentifier, ProductImage, SupplyBrand
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
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "code", "slug", "parent", "level", "is_active"); list_filter = ("is_active", "level"); search_fields = ("name_fa", "name_en", "code", "slug"); ordering = ("level", "code"); inlines = (CategoryAttributeInline,)
@admin.register(CategorySlugRedirect)
class CategorySlugRedirectAdmin(admin.ModelAdmin):
    list_display = ("old_slug", "category"); search_fields = ("old_slug", "category__name_fa", "category__slug")
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "brand", "category", "unit", "is_featured", "is_active"); list_filter = ("is_featured", "is_active", "brand", "category"); search_fields = ("code", "name", "slug", "identifiers__normalized_value", "documents__display_name"); ordering = ("code",); inlines = (ProductImageInline, ProductDocumentInline, InventoryInline, ProductPriceInline, ProductIdentifierInline, ProductAttributeValueInline); list_editable = ("is_featured",); autocomplete_fields = ("brand",)
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin): list_display = ("product", "is_primary", "sort_order"); list_filter = ("is_primary",); search_fields = ("product__code", "alt_text", "alt_fa", "alt_en")
@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ("display_name", "product", "document_type", "language", "revision", "file_size", "is_active", "is_published", "display_order")
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
class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ("category", "attribute", "is_required", "is_filterable", "unit_override", "display_order")
    list_filter = ("is_required", "is_filterable")
    search_fields = ("category__name_fa", "category__code", "attribute__name_fa", "attribute__code")
    autocomplete_fields = ("category", "attribute")
    ordering = ("category", "display_order", "attribute__name_fa")
