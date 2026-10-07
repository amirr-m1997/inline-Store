"""ادمین هسته: لاگ حسابرسی (فقط‌خواندنی) و اعلان‌ها."""
from __future__ import annotations

from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter

from core.admin_utils import ModelHelpMixin, PanelModelAdmin, badge, diff_cell, html_table
from core.utils import jalali_dt, num
from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter

from .models import AuditLog, Notification


@admin.register(AuditLog)
class AuditLogAdmin(ModelHelpMixin, ModelAdmin):
    """لاگ حسابرسی فقط‌خواندنی است: نه افزودن، نه ویرایش، نه حذف."""

    list_display = ("created_at_col", "action_badge", "object_repr", "model_name",
                    "actor_repr", "role", "diff_col", "ip")
    list_filter = (("action", ChoicesDropdownFilter), "model_name", "role",
                   ("actor", RelatedDropdownFilter), ("created_at", RangeDateFilter))
    search_fields = ("object_repr", "model_name", "actor_repr", "reason", "note", "object_id")
    date_hierarchy = "created_at"
    list_per_page = 50
    readonly_fields = ("action", "actor", "actor_repr", "role", "model_name", "object_id",
                       "object_repr", "before", "after", "changed_fields", "reason", "note",
                       "ip", "user_agent", "created_at", "diff_display")
    fieldsets = (
        ("رخداد", {"fields": (("created_at", "action"), ("model_name", "object_id"),
                              "object_repr", "reason")}),
        ("کاربر", {"fields": (("actor", "actor_repr"), "role", "ip", "user_agent")}),
        ("تغییرات", {"fields": ("diff_display", "changed_fields", "before", "after")}),
    )

    @admin.display(description="زمان", ordering="created_at")
    def created_at_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.display(description="اقدام", ordering="action")
    def action_badge(self, obj):
        colors = {
            "create": "#12855f", "update": "#1d4ed8", "delete": "#c02626",
            "status": "#0e7490", "price": "#6d28d9", "stock": "#0891b2",
            "login": "#12855f", "login_failed": "#c02626", "logout": "#64748b",
            "export": "#b45309", "import": "#b45309", "impersonate": "#6d28d9",
            "approve": "#12855f", "reject": "#c02626",
        }
        return badge(obj.get_action_display(), colors.get(obj.action, "#64748b"))

    @admin.display(description="تغییرات (قبل ← بعد)")
    def diff_col(self, obj):
        pairs = obj.diff_pairs[:2]
        if not pairs:
            return "—"
        html = ""
        for key, old, new in pairs:
            html += str(diff_cell(old, new)) + f' <span style="color:#5b6b82;font-size:11px">{key}</span><br>'
        return format_html("{}", format_html(html))

    @admin.display(description="جزئیات تغییرات")
    def diff_display(self, obj):
        pairs = obj.diff_pairs
        if not pairs:
            return obj.note or "—"
        rows = [[key, str(old), str(new)] for key, old, new in pairs]
        table = html_table(["فیلد", "قبل", "بعد"], rows)
        if obj.note:
            return format_html("{}<div style='margin-top:8px;color:#5b6b82'>{}</div>", table, obj.note)
        return table

    # --- قفل کردن همه‌ی عملیات تغییر
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(PanelModelAdmin, ModelAdmin):
    list_display = ("created_at_col", "level_badge", "kind_badge", "title", "company",
                    "is_read", "target_link")
    list_filter = (("level", ChoicesDropdownFilter), ("kind", ChoicesDropdownFilter),
                   "is_read", ("company", RelatedDropdownFilter))
    search_fields = ("title", "body", "dedup_key")
    autocomplete_fields = ("company",)
    actions = ["action_mark_read", "action_mark_unread"]

    @admin.display(description="رکورد مرتبط")
    def target_link(self, obj):
        """لینک مقصد اعلان؛ به‌جای نمایش نشانی خام، برچسب کوتاه «مشاهده» نشان داده می‌شود."""
        if not obj.url:
            return "—"
        return format_html('<a href="{}">مشاهده</a>', obj.url)
    list_editable = ("is_read",)
    date_hierarchy = "created_at"

    @admin.display(description="زمان", ordering="created_at")
    def created_at_col(self, obj):
        return jalali_dt(obj.created_at)

    @admin.display(description="شدت", ordering="level")
    def level_badge(self, obj):
        colors = {"info": "#1d4ed8", "success": "#12855f", "warning": "#b45309", "danger": "#c02626"}
        return badge(obj.get_level_display(), colors.get(obj.level, "#64748b"))

    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        return badge(obj.get_kind_display(), "#0e7490")

    @admin.action(description="علامت‌گذاری خوانده‌شده")
    def action_mark_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"{num(count)} اعلان خوانده‌شده شد.", messages.SUCCESS)

    @admin.action(description="علامت‌گذاری خوانده‌نشده")
    def action_mark_unread(self, request, queryset):
        queryset.update(is_read=False)
