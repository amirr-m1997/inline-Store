from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from core.admin_utils import ModelHelpMixin

from .models import Profile
from .roles import ROLE_MATRIX

admin.site.unregister(User)
admin.site.unregister(Group)

# نام‌های فارسی برای مدل‌های داخلی جنگو (روی خود مدل تنظیم می‌شود تا در همه‌جای پنل — عنوان صفحهٔ فهرست،
# دکمهٔ افزودن، تاریخچه و breadcrumb — یکسان دیده شود).
User._meta.verbose_name = "کاربر پنل"
User._meta.verbose_name_plural = "کاربران پنل"
Group._meta.verbose_name = "گروه دسترسی"
Group._meta.verbose_name_plural = "گروه‌های دسترسی"


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "پروفایل و دسترسی"


@admin.register(User)
class UserAdmin(ModelHelpMixin, BaseUserAdmin, ModelAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "full_name", "role_badge", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "profile__role")
    search_fields = ("username", "first_name", "last_name", "email")

    @admin.display(description="نام")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="نقش")
    def role_badge(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return "—"
        colors = {
            "sysadmin": "#7c3aed", "sales_manager": "#0e7490", "sales": "#0891b2",
            "warehouse": "#b45309", "finance": "#12855f", "content": "#64748b",
            "support": "#1d4ed8",
        }
        color = colors.get(profile.role, "#64748b")
        return format_html(
            '<span style="background:{}1a;color:{};padding:2px 9px;border-radius:999px;font-size:11.5px">{}</span>',
            color, color, profile.get_role_display(),
        )


@admin.register(Group)
class GroupAdmin(ModelHelpMixin, BaseGroupAdmin, ModelAdmin):
    search_fields = ("name",)
    filter_horizontal = ("permissions",)


@admin.register(Profile)
class ProfileAdmin(ModelHelpMixin, ModelAdmin):
    list_display = ("user", "role", "job_title", "branch", "can_approve_discount_upto",
                    "two_factor_enabled", "phone")
    list_filter = ("role", "two_factor_enabled", "branch")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
    list_editable = ("can_approve_discount_upto", "two_factor_enabled")
    autocomplete_fields = ("user",)
    fieldsets = (
        ("هویت", {"fields": ("user", "role", "job_title", "branch", "phone")}),
        ("اختیارات", {"fields": ("can_approve_discount_upto", "can_approve_order_upto")}),
        ("امنیت", {"fields": ("two_factor_enabled", "ip_allowlist")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
