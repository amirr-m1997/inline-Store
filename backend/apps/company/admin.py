from django.contrib import admin

from .models import CompanyAdvantage, CompanyInfo


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "phone", "mobile", "email")
    fieldsets = (
        ("اطلاعات شرکت", {"fields": ("name_fa", "logo", "description", "address", "phone", "mobile", "email", "website", "working_hours")} ),
        ("تنظیمات فوتر", {"fields": ("footer_copyright_fa", "footer_copyright_en")} ),
        ("تنظیمات هیرو", {"fields": ("hero_is_active", "hero_title_fa", "hero_title_en", "hero_slogan_fa", "hero_slogan_en", "hero_description_fa", "hero_description_en", "hero_image", "mobile_hero_image", "primary_button_text", "primary_button_link", "secondary_button_text", "secondary_button_link")} ),
    )

    def has_add_permission(self, request):
        return not CompanyInfo.objects.exists()


@admin.register(CompanyAdvantage)
class CompanyAdvantageAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "order", "is_active")
    list_editable = ("order", "is_active")
