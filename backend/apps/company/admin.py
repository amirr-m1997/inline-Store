from django.contrib import admin

from .models import Capability, CompanyAdvantage, CompanyCertification, CompanyHonor, CompanyInfo, CompanyLocation, CompanyMilestone, CompanySection, Industry
from .review import review_record


class TranslationMissingFilter(admin.SimpleListFilter):
    title = "ترجمه انگلیسی"
    parameter_name = "translation"

    def lookups(self, request, model_admin): return (("missing", "فاقد ترجمه"), ("present", "دارای ترجمه"))

    def queryset(self, request, queryset):
        if self.value() == "missing":
            return queryset.filter(title_en="") if hasattr(queryset.model, "title_en") else queryset.filter(name_en="")
        if self.value() == "present":
            return queryset.exclude(title_en="") if hasattr(queryset.model, "title_en") else queryset.exclude(name_en="")
        return queryset


class VerificationRequiredFilter(admin.SimpleListFilter):
    title = "نیازمند تأیید"
    parameter_name = "verification_required"

    def lookups(self, request, model_admin): return (("yes", "بله"), ("no", "خیر"))

    def queryset(self, request, queryset):
        if not hasattr(queryset.model, "verification_required"): return queryset
        return queryset.filter(verification_required=self.value() == "yes") if self.value() in {"yes", "no"} else queryset


class ReviewStatusFilter(admin.SimpleListFilter):
    title = "وضعیت بررسی"
    parameter_name = "review_status"

    def lookups(self, request, model_admin):
        return (("verification", "نیازمند تأیید"), ("editorial", "نیازمند کار تحریریه"), ("ready", "آماده تأیید کسب‌وکار"))

    def queryset(self, request, queryset):
        selected = self.value()
        if selected not in {"verification", "editorial", "ready"}:
            return queryset
        kind = queryset.model.__name__
        matching = []
        for item in queryset:
            status = review_record(kind, item)["status"]
            if ((selected == "verification" and status == "Needs verification") or
                    (selected == "editorial" and status == "Needs editorial work") or
                    (selected == "ready" and status == "Ready for business approval")):
                matching.append(item.pk)
        return queryset.filter(pk__in=matching)


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


@admin.register(CompanySection)
class CompanySectionAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "section_type", "order", "is_active", "is_published")
    list_filter = ("section_type", "is_active", "is_published", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("order", "is_active", "is_published")
    search_fields = ("title_fa", "title_en", "summary_fa", "summary_en")
    ordering = ("order", "id")


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "slug", "order", "is_active", "is_published")
    list_filter = ("is_active", "is_published", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("order", "is_active", "is_published")
    search_fields = ("title_fa", "title_en", "slug")
    filter_horizontal = ("categories", "products")
    prepopulated_fields = {"slug": ("title_fa",)}


@admin.register(CompanyLocation)
class CompanyLocationAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "location_type", "order", "is_active", "is_published", "verification_required")
    list_filter = ("location_type", "is_active", "is_published", "verification_required", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("order", "is_active", "is_published")
    search_fields = ("name_fa", "name_en", "address_fa", "address_en", "phone", "email", "source_title")
    ordering = ("order", "id")


@admin.register(CompanyMilestone)
class CompanyMilestoneAdmin(admin.ModelAdmin):
    list_display = ("date_label", "title_fa", "order", "is_published", "verification_required")
    list_filter = ("is_published", "verification_required", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("order", "is_published")
    search_fields = ("date_label", "title_fa", "title_en", "source_title")


@admin.register(CompanyCertification)
class CompanyCertificationAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "issuer", "certificate_code", "verification_status", "is_published", "order")
    list_filter = ("verification_status", "is_published", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("verification_status", "is_published", "order")
    search_fields = ("title_fa", "title_en", "issuer", "certificate_code", "source_title")


@admin.register(CompanyHonor)
class CompanyHonorAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "issuer", "year_label", "is_published", "verification_required", "order")
    list_filter = ("is_published", "verification_required", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("is_published", "verification_required", "order")
    search_fields = ("title_fa", "title_en", "issuer", "year_label", "source_title")


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "slug", "order", "is_active", "is_published")
    list_filter = ("is_active", "is_published", TranslationMissingFilter, ReviewStatusFilter)
    list_editable = ("order", "is_active", "is_published")
    search_fields = ("name_fa", "name_en", "slug", "source_title")
    filter_horizontal = ("categories", "products", "capabilities")
    prepopulated_fields = {"slug": ("name_fa",)}
