from django.contrib import admin

from .models import NotificationDelivery


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("event_type", "channel", "masked_recipient", "status", "related_reference", "attempt_count", "created_at", "sent_at")
    list_filter = ("event_type", "channel", "status", "created_at")
    search_fields = ("related_reference", "recipient")
    readonly_fields = tuple(field.name for field in NotificationDelivery._meta.fields)
    date_hierarchy = "created_at"

    @admin.display(description="گیرنده")
    def masked_recipient(self, obj):
        value = obj.recipient or ""
        if "@" in value:
            local, domain = value.split("@", 1)
            return f"{local[:1]}***@{domain}"
        return f"{value[:2]}*****{value[-4:]}" if len(value) > 6 else "***"
