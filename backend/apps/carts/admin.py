from django.contrib import admin
from .models import Cart, CartItem, DiscountCode
class CartItemInline(admin.TabularInline): model = CartItem; extra = 0
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin): list_display = ("id", "user", "customer_phone", "discount_code", "final_total", "status", "updated_at"); list_filter = ("status", "discount_code", "shipping_province"); search_fields = ("user__username", "user__email", "guest_token", "customer_phone", "customer_last_name"); inlines = (CartItemInline,)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin): list_display = ("cart", "product", "quantity", "updated_at"); search_fields = ("product__code", "product__name")
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "percentage", "minimum_order_amount", "valid_from", "valid_until", "usage_count", "max_uses", "is_active"); list_filter = ("is_active",); search_fields = ("code",); readonly_fields = ("usage_count", "created_at", "updated_at")
