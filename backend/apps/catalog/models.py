from django.core.exceptions import ValidationError
from django.db import models
from .slugs import latin_category_slug

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class Category(TimestampedModel):
    code = models.CharField(max_length=64)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.PROTECT)
    level = models.PositiveSmallIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("parent", "code"), name="category_parent_code_unique"), models.UniqueConstraint(fields=("parent", "slug"), name="category_parent_slug_unique")]
        ordering = ("parent_id", "code")
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
    def clean(self):
        if self.parent_id and self.parent_id == self.pk: raise ValidationError("A category cannot be its own parent.")
        ancestor = self.parent
        while ancestor:
            if ancestor.pk == self.pk:
                raise ValidationError("A category cannot be moved beneath one of its descendants.")
            ancestor = ancestor.parent
    def save(self, *args, **kwargs):
        if not self.slug:
            base = latin_category_slug(self.name_fa)
            slug, suffix = base, 2
            while Category.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug, suffix = f"{base}-{suffix}", suffix + 1
            self.slug = slug
        self.level = self.parent.level + 1 if self.parent_id else 0
        self.full_clean()
        super().save(*args, **kwargs)
    def descendant_ids(self, include_self=True):
        ids = [self.pk] if include_self else []
        frontier = [self.pk]
        while frontier:
            frontier = list(Category.objects.filter(parent_id__in=frontier, is_active=True).values_list("id", flat=True))
            ids.extend(frontier)
        return ids
    def __str__(self): return self.name_fa

class CategorySlugRedirect(TimestampedModel):
    old_slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, related_name="slug_redirects", on_delete=models.CASCADE)

    class Meta:
        ordering = ("old_slug",)
        verbose_name = "نشانی قدیمی دسته‌بندی"
        verbose_name_plural = "نشانی‌های قدیمی دسته‌بندی"

    def __str__(self): return f"{self.old_slug} → {self.category.slug}"

class Product(TimestampedModel):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    unit = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    technical_specs = models.JSONField(default=dict, blank=True)
    is_featured = models.BooleanField("نمایش در محصولات منتخب", default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ("name",)
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
    def __str__(self): return f"{self.code} — {self.name}"

class SupplyBrand(TimestampedModel):
    name = models.CharField("نام برند", max_length=120, unique=True)
    logo = models.ImageField("لوگو", upload_to="brands/", blank=True, null=True)
    website = models.URLField("وب‌سایت", blank=True)
    order = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "برند قابل تأمین"
        verbose_name_plural = "برندهای قابل تأمین"

    def __str__(self): return self.name

class ProductImage(TimestampedModel):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=255, blank=True)
    alt_fa = models.CharField(max_length=255, blank=True)
    alt_en = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"

    def __str__(self):
        return f"{self.product.code} — {self.sort_order}"
