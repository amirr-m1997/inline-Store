from django.contrib import admin
from .models import ProductPrice, CurrencyRate
@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin): list_display = ("product", "amount", "currency", "effective_from", "effective_to", "source"); list_filter = ("currency",); search_fields = ("product__code", "product__name", "source"); ordering = ("-effective_from",)
@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin): list_display = ("currency", "rate_to_irr", "rate_date", "source"); list_filter = ("currency",); search_fields = ("source",); ordering = ("-rate_date",)

