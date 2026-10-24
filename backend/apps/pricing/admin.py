from django.contrib import admin
from .models import CurrencyRate, CustomerPriceList, CustomerPriceListItem, ProductPrice
@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin): list_display = ("product", "amount", "currency", "effective_from", "effective_to", "source"); list_filter = ("currency",); search_fields = ("product__code", "product__name", "source"); ordering = ("-effective_from",)
@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin): list_display = ("currency", "rate_to_irr", "rate_date", "source"); list_filter = ("currency",); search_fields = ("source",); ordering = ("-rate_date",)


class CustomerPriceListItemInline(admin.TabularInline):
    model = CustomerPriceListItem
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("product", "minimum_quantity", "fixed_amount", "discount_percentage")


@admin.register(CustomerPriceList)
class CustomerPriceListAdmin(admin.ModelAdmin):
    list_display = ("name", "customer", "currency", "priority", "valid_from", "valid_until", "is_active", "item_count")
    list_filter = ("is_active", "currency", "valid_from", "valid_until")
    search_fields = ("name", "customer__company_name", "customer__email", "customer__phone")
    autocomplete_fields = ("customer",)
    inlines = (CustomerPriceListItemInline,)

    @admin.display(description="تعداد اقلام")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(CustomerPriceListItem)
class CustomerPriceListItemAdmin(admin.ModelAdmin):
    list_display = ("price_list", "product", "minimum_quantity", "fixed_amount", "discount_percentage", "updated_at")
    list_filter = ("price_list__currency",)
    search_fields = ("price_list__name", "product__code", "product__name")
    autocomplete_fields = ("price_list", "product")

