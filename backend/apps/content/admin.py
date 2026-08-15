from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q

from .models import ContentArticle, ContentCategory, FAQEntry
from .review import evaluate_record


class MissingFieldFilter(admin.SimpleListFilter):
    title = "کیفیت محتوا"
    parameter_name = "quality"

    def lookups(self, request, model_admin):
        return (("translation", "ترجمه ناقص"), ("seo", "سئوی ناقص"), ("image", "تصویر ناقص"), ("source", "بدون منبع"), ("relationships", "بدون ارتباط"))

    def queryset(self, request, queryset):
        value = self.value()
        if value == "translation":
            fields = Q(question_en="") if queryset.model is FAQEntry else Q(title_en="")
            return queryset.filter(fields)
        if value == "seo" and queryset.model is ContentArticle:
            return queryset.filter(Q(seo_title_fa="") | Q(seo_description_fa=""))
        if value == "image" and queryset.model is ContentArticle:
            return queryset.filter(Q(featured_image="") | Q(featured_image__isnull=True))
        if value == "source":
            return queryset.filter(source_url="")
        if value == "relationships":
            if queryset.model is ContentArticle:
                return queryset.annotate(related_count=Count("products", distinct=True) + Count("catalog_categories", distinct=True) + Count("brands", distinct=True) + Count("industries", distinct=True) + Count("capabilities", distinct=True)).filter(related_count=0)
            return queryset.annotate(related_count=Count("products", distinct=True) + Count("categories", distinct=True) + Count("industries", distinct=True) + Count("capabilities", distinct=True) + Count("articles", distinct=True)).filter(related_count=0)
        return queryset


class ProvenanceFilter(admin.SimpleListFilter):
    title = "منبع"
    parameter_name = "provenance"

    def lookups(self, request, model_admin):
        return (("imported", "واردشده"), ("manual", "بدون نشان واردات"), ("demo", "دمو"))

    def queryset(self, request, queryset):
        if self.value() == "imported": return queryset.exclude(source_fingerprint="")
        if self.value() == "manual": return queryset.filter(source_fingerprint="")
        if self.value() == "demo": return queryset.filter(migration_notes__icontains="demo-content:")
        return queryset


def quality_summary(obj):
    result = evaluate_record(obj)
    count = len(result["missing"]) + len(result["warnings"])
    return f"{count} هشدار" if count else "آماده بررسی"
quality_summary.short_description = "خلاصه کیفیت"


def quality_details(obj):
    result = evaluate_record(obj)
    parts = [f"وضعیت بررسی: {result['review_status']}"]
    if result["missing"]:
        parts.append("موارد ناقص: " + ", ".join(result["missing"]))
    if result["warnings"]:
        parts.append("هشدارها: " + ", ".join(result["warnings"]))
    if not result["missing"] and not result["warnings"]:
        parts.append("بدون هشدار تشخیصی")
    return " | ".join(parts)


quality_details.short_description = "گزارش کیفیت (فقط خواندنی)"


def public_view_link(obj):
    if not obj.is_active or not obj.is_published or not obj.published_at:
        return "—"
    return format_html('<a href="/fa/knowledge/{}/" target="_blank" rel="noopener">مشاهده عمومی</a>', obj.slug)


public_view_link.short_description = "لینک عمومی"


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "slug", "display_order", "is_active", "is_published")
    list_filter = ("is_active", "is_published")
    list_editable = ("display_order", "is_active", "is_published")
    search_fields = ("name_fa", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_fa",)}
    fieldsets = (("موضوع", {"fields": ("slug", "name_fa", "name_en", "description_fa", "description_en", "display_order", "is_active", "is_published")} ), ("منبع و مهاجرت", {"fields": ("source_url", "source_title", "migration_notes")} ))


@admin.register(ContentArticle)
class ContentArticleAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "content_type", "category", "review_status", "published_at", "is_published", "is_featured", quality_summary, public_view_link, "display_order")
    list_filter = ("content_type", "review_status", "is_active", "is_published", "is_featured", "category", MissingFieldFilter, ProvenanceFilter)
    list_editable = ("is_published", "is_featured", "display_order")
    search_fields = ("title_fa", "title_en", "excerpt_fa", "excerpt_en", "slug")
    ordering = ("display_order", "-published_at", "-id")
    prepopulated_fields = {"slug": ("title_fa",)}
    autocomplete_fields = ("author", "category", "products", "catalog_categories", "brands", "industries", "capabilities")
    readonly_fields = (quality_details, public_view_link)
    fieldsets = (
        ("محتوا", {"fields": ("content_type", "slug", "title_fa", "title_en", "excerpt_fa", "excerpt_en", "body_fa", "body_en", "featured_image")} ),
        ("انتشار و بررسی", {"fields": ("is_active", "is_published", "review_status", "is_featured", "published_at", "display_order", "author")} ),
        ("موضوع و ارتباط با کسب‌وکار", {"fields": ("category", "products", "catalog_categories", "brands", "industries", "capabilities")} ),
        ("سئو", {"fields": ("seo_title_fa", "seo_title_en", "seo_description_fa", "seo_description_en")} ),
        ("منبع و مهاجرت", {"fields": ("source_url", "source_title", "migration_notes")} ),
        ("بازبینی کیفیت", {"fields": (quality_details, public_view_link)}),
    )


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ("question_fa", "faq_type", "review_status", "display_order", "is_active", "is_published", quality_summary)
    list_filter = ("faq_type", "review_status", "is_active", "is_published", MissingFieldFilter, ProvenanceFilter)
    list_editable = ("display_order", "is_active", "is_published")
    search_fields = ("question_fa", "question_en", "answer_fa", "answer_en", "slug")
    ordering = ("display_order", "id")
    prepopulated_fields = {"slug": ("question_fa",)}
    autocomplete_fields = ("products", "categories", "industries", "capabilities", "articles")
    readonly_fields = (quality_details,)
    fieldsets = (
        ("سوال و پاسخ", {"fields": ("slug", "faq_type", "question_fa", "question_en", "answer_fa", "answer_en")} ),
        ("انتشار و بررسی", {"fields": ("is_active", "is_published", "review_status", "display_order")} ),
        ("ارتباط با کسب‌وکار", {"fields": ("products", "categories", "industries", "capabilities", "articles")} ),
        ("منبع و مهاجرت", {"fields": ("source_url", "source_title", "migration_notes")} ),
        ("بازبینی کیفیت", {"fields": (quality_details,)}),
    )
