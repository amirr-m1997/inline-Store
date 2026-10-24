from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "object_repr", "app_label", "model_name", "actor", "request_path")
    list_filter = ("action", "app_label", "model_name", "created_at")
    search_fields = ("object_repr", "object_id", "actor__username", "request_path")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at", "actor", "action", "app_label", "model_name", "object_id",
        "object_repr", "changes", "request_method", "request_path", "remote_addr",
    )
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in ("GET", "HEAD")
