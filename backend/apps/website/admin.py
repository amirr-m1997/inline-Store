from django.contrib import admin

from .models import ContactMessage, CustomerFeedback, CustomerSupportRequest, FooterLink, FooterSection, SiteNavigation, TrustBadge, WarrantyPolicy, WarrantyRegistration


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

@admin.register(WarrantyPolicy)
class WarrantyPolicyAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "title_en", "registration_enabled", "is_published", "updated_at")
    list_filter = ("is_published", "registration_enabled")
    search_fields = ("title_fa", "title_en", "body_fa", "body_en")
    ordering = ("-updated_at",)
    readonly_fields = ("updated_at",)

@admin.register(WarrantyRegistration)
class WarrantyRegistrationAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "phone", "product", "order", "serial_number", "status", "submitted_at")
    list_filter = ("status", "product", "submitted_at")
    search_fields = ("reference", "full_name", "phone", "email", "serial_number")
    autocomplete_fields = ("customer", "product", "order")
    readonly_fields = ("reference", "submitted_at")
    date_hierarchy = "submitted_at"

@admin.register(CustomerSupportRequest)
class CustomerSupportRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "request_type", "subject", "customer", "product", "order", "status", "submitted_at")
    list_filter = ("status", "request_type", "product", "submitted_at")
    search_fields = ("reference", "subject", "full_name", "phone", "email", "message")
    autocomplete_fields = ("customer", "product", "order")
    readonly_fields = ("reference", "submitted_at", "updated_at")
    date_hierarchy = "submitted_at"

@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ("feedback_type", "rating", "customer", "order", "submitted_at")
    list_filter = ("feedback_type", "rating", "submitted_at")
    search_fields = ("message", "customer__username", "customer__email")
    autocomplete_fields = ("customer", "order")
    readonly_fields = ("submitted_at",)
    date_hierarchy = "submitted_at"
