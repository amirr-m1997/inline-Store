import os
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.core.files.uploadedfile import UploadedFile
from .slugs import latin_category_slug
from .search_normalization import normalize_search_text

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
    def __str__(self):
        """Keep admin/autocomplete labels understandable in a large catalog."""
        parts = []
        current = self
        while current is not None:
            parts.append(current.name_fa)
            current = current.parent
        return " / ".join(reversed(parts))

class CategorySlugRedirect(TimestampedModel):
    old_slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, related_name="slug_redirects", on_delete=models.CASCADE)

    class Meta:
        ordering = ("old_slug",)
        verbose_name = "نشانی قدیمی دسته‌بندی"
        verbose_name_plural = "نشانی‌های قدیمی دسته‌بندی"

    def __str__(self): return f"{self.old_slug} → {self.category.slug}"

class ProductBrand(TimestampedModel):
    """Manufacturer/brand metadata owned by the product catalog domain."""
    name = models.CharField(max_length=160, unique=True)
    code = models.CharField(max_length=64, unique=True, blank=True, null=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True, null=True)
    logo = models.ImageField(upload_to="product-brands/", blank=True, null=True)
    description_fa = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    seo_title_fa = models.CharField(max_length=255, blank=True)
    seo_title_en = models.CharField(max_length=255, blank=True)
    seo_description_fa = models.CharField(max_length=500, blank=True)
    seo_description_en = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "برند / سازنده محصول"
        verbose_name_plural = "برندها / سازندگان محصول"

    def __str__(self): return self.name


class Product(TimestampedModel):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    unit = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    technical_specs = models.JSONField(default=dict, blank=True)
    brand = models.ForeignKey(ProductBrand, null=True, blank=True, related_name="products", on_delete=models.SET_NULL)
    is_featured = models.BooleanField("نمایش در محصولات منتخب", default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=("is_active", "category"), name="cat_prod_active_cat_idx"),
            models.Index(fields=("is_active", "created_at", "id"), name="cat_prod_active_created_idx"),
            models.Index(fields=("is_active", "is_featured"), name="cat_prod_active_featured_idx"),
        ]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
    def __str__(self): return f"{self.code} — {self.name}"


DOCUMENT_MAX_SIZE = 25 * 1024 * 1024
DOCUMENT_EXTENSIONS = {
    "datasheet": {"pdf"},
    "manual": {"pdf", "doc", "docx"},
    "cad": {"dwg", "dxf", "step", "stp", "iges", "igs"},
    "certificate": {"pdf"},
    "catalogue": {"pdf", "doc", "docx", "zip"},
    "other": {"pdf", "doc", "docx", "xls", "xlsx", "zip"},
}
DOCUMENT_MIME_TYPES = {
    "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip", "application/octet-stream", "image/vnd.dwg", "image/vnd.dxf",
}


def validate_product_document_file(uploaded_file):
    name = os.path.basename(uploaded_file.name or "")
    if name != uploaded_file.name or re.search(r"[\x00-\x1f\\/]", name):
        raise ValidationError("Document filenames must be safe and contain no path components.")
    if uploaded_file.size > DOCUMENT_MAX_SIZE:
        raise ValidationError("Document files must be 25 MB or smaller.")
    extension = os.path.splitext(name)[1].lower().lstrip(".")
    if not extension:
        raise ValidationError("Document files must include an allowed extension.")
    if isinstance(uploaded_file, UploadedFile) and uploaded_file.content_type and uploaded_file.content_type not in DOCUMENT_MIME_TYPES:
        raise ValidationError("The document MIME type is not allowed.")


class ProductDocument(TimestampedModel):
    class DocumentType(models.TextChoices):
        DATASHEET = "datasheet", "دیتاشیت"
        MANUAL = "manual", "راهنما"
        CAD = "cad", "CAD"
        CERTIFICATE = "certificate", "گواهی‌نامه"
        CATALOGUE = "catalogue", "کاتالوگ"
        OTHER = "other", "سایر"

    product = models.ForeignKey(Product, related_name="documents", on_delete=models.CASCADE)
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    title_fa = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="product-documents/%Y/%m/", validators=[validate_product_document_file])
    display_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=127, blank=True, editable=False)
    file_size = models.PositiveBigIntegerField(default=0, editable=False)
    language = models.CharField(max_length=16, blank=True)
    revision = models.CharField(max_length=64, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("display_order", "id")
        verbose_name = "سند فنی محصول"
        verbose_name_plural = "اسناد فنی محصولات"

    def clean(self):
        super().clean()
        extension = os.path.splitext(self.file.name or "")[1].lower().lstrip(".")
        if extension and extension not in DOCUMENT_EXTENSIONS.get(self.document_type, set()):
            raise ValidationError({"file": "This file extension is not allowed for the selected document type."})
        if self.display_name and re.search(r"[\x00-\x1f\\/]", self.display_name):
            raise ValidationError({"display_name": "Display names must not contain path components or control characters."})

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.mime_type = getattr(self.file, "content_type", "") or self.mime_type
            if not self.display_name:
                self.display_name = os.path.basename(self.file.name)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.title_fa or self.title_en or os.path.basename(self.file.name)


def normalize_identifier(value):
    """Keep a display value intact while making identifier lookups deterministic."""
    return normalize_search_text(value)


class ProductIdentifier(TimestampedModel):
    class Type(models.TextChoices):
        INTERNAL_CODE = "internal_code", "کد داخلی محصول"
        SKU = "sku", "شناسه SKU"
        MANUFACTURER_PART_NUMBER = "mpn", "شماره قطعه سازنده"
        BARCODE = "barcode", "بارکد"
        ALIAS = "alias", "نام مستعار"

    product = models.ForeignKey(Product, related_name="identifiers", on_delete=models.CASCADE)
    identifier_type = models.CharField(max_length=24, choices=Type.choices)
    normalized_value = models.CharField(max_length=255)
    display_value = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=("identifier_type", "normalized_value"), name="cat_ident_type_value_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=("identifier_type", "normalized_value"),
                condition=~models.Q(identifier_type="alias"),
                name="cat_identifier_unique_non_alias",
            ),
            models.UniqueConstraint(fields=("product", "identifier_type", "normalized_value"), name="cat_identifier_product_unique"),
        ]
        verbose_name = "شناسه محصول"
        verbose_name_plural = "شناسه‌های محصول"

    def clean(self):
        if not self.normalized_value:
            raise ValidationError({"normalized_value": "شناسه محصول نمی‌تواند خالی باشد."})
        if not self.display_value:
            self.display_value = self.normalized_value

    def save(self, *args, **kwargs):
        self.normalized_value = normalize_identifier(self.normalized_value or self.display_value)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self): return f"{self.product.code} — {self.display_value}"


class AttributeDefinition(TimestampedModel):
    class ValueType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        BOOLEAN = "boolean", "Boolean"
        ENUM = "enum", "Enum"

    code = models.SlugField(max_length=96, unique=True)
    name_fa = models.CharField(max_length=160)
    name_en = models.CharField(max_length=160, blank=True)
    value_type = models.CharField(max_length=16, choices=ValueType.choices)
    unit = models.CharField(max_length=32, blank=True)
    is_filterable = models.BooleanField(default=False)
    is_comparable = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "name_fa")
        verbose_name = "تعریف مشخصه فنی"
        verbose_name_plural = "تعریف‌های مشخصه فنی"

    def __str__(self): return self.name_fa


class CategoryAttribute(TimestampedModel):
    category = models.ForeignKey(Category, related_name="attribute_settings", on_delete=models.CASCADE)
    attribute = models.ForeignKey(AttributeDefinition, related_name="category_settings", on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    is_filterable = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    unit_override = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ("display_order", "attribute__name_fa")
        constraints = [models.UniqueConstraint(fields=("category", "attribute"), name="cat_category_attribute_unique")]
        indexes = [models.Index(fields=("category", "display_order"), name="cat_category_attr_order_idx")]
        verbose_name = "مشخصه دسته‌بندی"
        verbose_name_plural = "مشخصه‌های دسته‌بندی"

    def __str__(self): return f"{self.category} — {self.attribute}"


class ProductAttributeValue(TimestampedModel):
    product = models.ForeignKey(Product, related_name="attribute_values", on_delete=models.CASCADE)
    attribute = models.ForeignKey(AttributeDefinition, related_name="product_values", on_delete=models.PROTECT)
    text_value = models.TextField(blank=True)
    number_value = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    enum_value = models.CharField(max_length=160, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("product", "attribute"), name="cat_product_attribute_unique")]
        indexes = [
            models.Index(fields=("attribute", "number_value"), name="cat_attr_number_value_idx"),
            models.Index(fields=("attribute", "enum_value"), name="cat_attr_enum_value_idx"),
        ]
        verbose_name = "مقدار مشخصه محصول"
        verbose_name_plural = "مقادیر مشخصه محصول"

    def clean(self):
        if not self.attribute_id:
            return
        values = {
            AttributeDefinition.ValueType.TEXT: self.text_value,
            AttributeDefinition.ValueType.NUMBER: self.number_value,
            AttributeDefinition.ValueType.BOOLEAN: self.boolean_value,
            AttributeDefinition.ValueType.ENUM: self.enum_value,
        }
        expected = values[self.attribute.value_type]
        if expected in (None, ""):
            raise ValidationError("مقدار متناسب با نوع مشخصه الزامی است.")
        if any(value not in (None, "") for value_type, value in values.items() if value_type != self.attribute.value_type):
            raise ValidationError("فقط مقدار متناسب با نوع مشخصه قابل ثبت است.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self): return f"{self.product.code} — {self.attribute.code}"

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
        indexes = [models.Index(fields=("product", "is_primary", "sort_order"), name="cat_image_primary_idx")]
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"

    def __str__(self):
        return f"{self.product.code} — {self.sort_order}"
