from django.contrib import admin
from apps.inventory.models import Inventory
from apps.pricing.models import ProductPrice
from .models import Category, CategorySlugRedirect, Product, ProductImage, SupplyBrand
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_fa", "alt_en", "is_primary", "sort_order")
class InventoryInline(admin.StackedInline): model = Inventory; extra = 0; max_num = 1
class ProductPriceInline(admin.TabularInline): model = ProductPrice; extra = 0
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "code", "slug", "parent", "level", "is_active"); list_filter = ("is_active", "level"); search_fields = ("name_fa", "name_en", "code", "slug"); ordering = ("level", "code")
@admin.register(CategorySlugRedirect)
class CategorySlugRedirectAdmin(admin.ModelAdmin):
    list_display = ("old_slug", "category"); search_fields = ("old_slug", "category__name_fa", "category__slug")
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "unit", "is_featured", "is_active"); list_filter = ("is_featured", "is_active", "category"); search_fields = ("code", "name", "slug"); ordering = ("code",); inlines = (ProductImageInline, InventoryInline, ProductPriceInline); list_editable = ("is_featured",)
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin): list_display = ("product", "is_primary", "sort_order"); list_filter = ("is_primary",); search_fields = ("product__code", "alt_text", "alt_fa", "alt_en")
@admin.register(SupplyBrand)
class SupplyBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active"); list_editable = ("order", "is_active"); search_fields = ("name",); ordering = ("order", "name")
