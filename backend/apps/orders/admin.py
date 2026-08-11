from django.contrib import admin

from .models import Invoice, InvoiceEmailLog, Order, OrderItem, OrderStatusHistory, Payment, ProformaRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "product_code", "unit", "unit_price", "quantity", "discount_percentage", "discount_amount", "line_subtotal", "line_total")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("gateway", "amount", "authority", "reference_id", "status", "created_at", "verified_at")


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "description", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "status", "final_amount", "currency", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("order_number", "customer_phone", "customer_email", "customer_company_name")
    readonly_fields = ("order_number", "subtotal", "discount_amount", "shipping_cost", "final_amount", "paid_at", "shipped_at", "delivered_at", "created_at", "updated_at")
    inlines = (OrderItemInline, PaymentInline, OrderStatusHistoryInline)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_code", "product_name", "quantity", "line_total")
    search_fields = ("order__order_number", "product_code", "product_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "gateway", "amount", "status", "authority", "reference_id", "created_at", "verified_at")
    list_filter = ("gateway", "status")
    search_fields = ("order__order_number", "authority", "reference_id")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "order", "customer_name", "final_amount", "created_at")
    search_fields = ("invoice_number", "order__order_number", "customer_name")
    readonly_fields = ("items_snapshot", "created_at")


@admin.register(InvoiceEmailLog)
class InvoiceEmailLogAdmin(admin.ModelAdmin):
    list_display = ("invoice", "recipient", "success", "created_at")
    readonly_fields = ("invoice", "recipient", "success", "error_message", "created_at")


@admin.register(ProformaRequest)
class ProformaRequestAdmin(admin.ModelAdmin):
    list_display = ("order", "customer", "status", "requested_at", "updated_at")
    list_filter = ("status", "requested_at")
    search_fields = ("order__order_number", "customer__email", "customer__phone")
    readonly_fields = ("order", "customer", "customer_note", "requested_at", "updated_at")
