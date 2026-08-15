from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class ContentCategory(models.Model):
    slug = models.SlugField(max_length=180, unique=True)
    name_fa = models.CharField(max_length=180)
    name_en = models.CharField(max_length=180, blank=True)
    description_fa = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    source_url = models.URLField(blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    migration_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("display_order", "name_fa", "id")
        verbose_name = "موضوع محتوایی"
        verbose_name_plural = "موضوع‌های محتوایی"

    def __str__(self):
        return self.name_fa


class ContentArticle(models.Model):
    class ReviewStatus(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        NEEDS_REVIEW = "needs_review", "نیازمند بررسی"
        READY = "ready", "آماده انتشار"

    class ContentType(models.TextChoices):
        NEWS = "news", "خبر"
        EVENT = "event", "رویداد"
        TECHNICAL_ARTICLE = "technical_article", "مقاله فنی"
        PRODUCT_GUIDE = "product_guide", "راهنمای محصول"
        BUYING_GUIDE = "buying_guide", "راهنمای خرید"
        PRODUCT_ANNOUNCEMENT = "product_announcement", "معرفی محصول"

    content_type = models.CharField(max_length=32, choices=ContentType.choices, db_index=True)
    slug = models.SlugField(max_length=220, unique=True)
    title_fa = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255, blank=True)
    excerpt_fa = models.CharField(max_length=500, blank=True)
    excerpt_en = models.CharField(max_length=500, blank=True)
    body_fa = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    featured_image = models.ImageField(upload_to="content/featured/%Y/%m/", blank=True, null=True,
                                       validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])])
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT, db_index=True)
    seo_title_fa = models.CharField(max_length=255, blank=True)
    seo_title_en = models.CharField(max_length=255, blank=True)
    seo_description_fa = models.CharField(max_length=500, blank=True)
    seo_description_en = models.CharField(max_length=500, blank=True)
    source_url = models.URLField(blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    migration_notes = models.TextField(blank=True)
    source_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="content_articles")
    category = models.ForeignKey(ContentCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="articles")
    products = models.ManyToManyField("catalog.Product", blank=True, related_name="content_articles")
    catalog_categories = models.ManyToManyField("catalog.Category", blank=True, related_name="content_articles")
    brands = models.ManyToManyField("catalog.ProductBrand", blank=True, related_name="content_articles")
    industries = models.ManyToManyField("company.Industry", blank=True, related_name="content_articles")
    capabilities = models.ManyToManyField("company.Capability", blank=True, related_name="content_articles")

    class Meta:
        ordering = ("display_order", "-published_at", "-id")
        indexes = [
            models.Index(fields=("is_active", "is_published", "published_at"), name="content_publication_idx"),
            models.Index(fields=("content_type", "display_order"), name="content_type_order_idx"),
        ]
        verbose_name = "مقاله / محتوای تحریریه"
        verbose_name_plural = "مقالات / محتوای تحریریه"

    def __str__(self):
        return self.title_fa


class FAQEntry(models.Model):
    class ReviewStatus(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        NEEDS_REVIEW = "needs_review", "نیازمند بررسی"
        READY = "ready", "آماده انتشار"

    class FAQType(models.TextChoices):
        GENERAL = "general", "عمومی"
        PRODUCT = "product", "محصول"
        TECHNICAL = "technical", "فنی"
        WARRANTY = "warranty", "گارانتی"
        ORDERING = "ordering", "سفارش"
        SUPPORT = "support", "پشتیبانی"
        INSTALLATION = "installation", "نصب"
        MAINTENANCE = "maintenance", "نگهداری"

    slug = models.SlugField(max_length=220, unique=True)
    question_fa = models.CharField(max_length=500)
    question_en = models.CharField(max_length=500, blank=True)
    answer_fa = models.TextField()
    answer_en = models.TextField(blank=True)
    faq_type = models.CharField(max_length=24, choices=FAQType.choices, default=FAQType.GENERAL, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_url = models.URLField(blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    migration_notes = models.TextField(blank=True)
    source_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    products = models.ManyToManyField("catalog.Product", blank=True, related_name="faq_entries")
    categories = models.ManyToManyField("catalog.Category", blank=True, related_name="faq_entries")
    industries = models.ManyToManyField("company.Industry", blank=True, related_name="faq_entries")
    capabilities = models.ManyToManyField("company.Capability", blank=True, related_name="faq_entries")
    articles = models.ManyToManyField(ContentArticle, blank=True, related_name="faq_entries")

    class Meta:
        ordering = ("display_order", "id")
        indexes = [
            models.Index(fields=("is_active", "is_published", "faq_type", "display_order"), name="content_faq_public_idx"),
        ]
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"

    def __str__(self):
        return self.question_fa
