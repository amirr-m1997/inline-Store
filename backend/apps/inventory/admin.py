from django.contrib import admin
from .models import Inventory, Receipt, Issue, Reservation
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "on_hand_quantity", "reserved_quantity", "available", "updated_at")
    search_fields = ("product__code", "product__name")
    list_filter = ("updated_at",)

    @admin.display(description="Available", ordering="on_hand_quantity")
    def available(self, obj):
        return obj.available_quantity
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin): list_display = ("product", "quantity", "occurred_at", "reference"); list_filter = ("occurred_at",); search_fields = ("product__code", "reference"); ordering = ("-occurred_at",)
@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin): list_display = ("product", "quantity", "occurred_at", "reference"); list_filter = ("occurred_at",); search_fields = ("product__code", "reference"); ordering = ("-occurred_at",)
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin): list_display = ("product", "order_item", "cart_item", "quantity", "status", "expires_at"); list_filter = ("status",); search_fields = ("product__code", "order_item__order__order_number"); ordering = ("-created_at",)
