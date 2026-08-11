from django.contrib import admin

from .models import ContactMessage, FooterLink, FooterSection, SiteNavigation, TrustBadge


@admin.register(SiteNavigation)
class SiteNavigationAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "url", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title_fa", "title_en", "url")


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1
    fields = ("title_fa", "title_en", "url", "order", "is_active", "open_in_new_tab")


@admin.register(FooterSection)
class FooterSectionAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title_fa", "title_en")
    inlines = (FooterLinkInline,)


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "section", "url", "order", "is_active", "open_in_new_tab")
    list_filter = ("section", "is_active", "open_in_new_tab")
    list_editable = ("order", "is_active")
    search_fields = ("title_fa", "title_en", "url")


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "order", "is_active", "image")
    list_editable = ("order", "is_active")
    search_fields = ("title_fa", "title_en", "alt_fa", "alt_en")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("full_name", "phone", "email", "subject", "message")
    readonly_fields = ("created_at", "updated_at")
