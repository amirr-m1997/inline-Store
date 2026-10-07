"""کاتالوگ صنعتی: دسته‌بندی، برند، قالب مشخصات فنی، محصول و اسناد."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.palette import ACCENT, DANGER, INFO, MUTED, OK, VIOLET, WARN

UOM_CHOICES = [
    ("device", "دستگاه"),
    ("set", "ست"),
    ("piece", "عدد"),
    ("branch", "شاخه"),
    ("meter", "متر"),
    ("kg", "کیلوگرم"),
    ("roll", "رول"),
    ("pack", "بسته"),
    ("liter", "لیتر"),
]

AVAILABILITY_CHOICES = [
    ("in_stock", "موجود (نو)"),
    ("ready", "آماده تحویل"),
    ("made_to_order", "ساخت به سفارش"),
    ("used", "کارکرده"),
    ("needs_quote", "نیازمند استعلام"),
    ("discontinued", "متوقف تولید"),
]

DOCUMENT_KINDS = [
    ("datasheet", "دیتاشیت فنی"),
    ("drawing", "نقشه ابعادی"),
    ("cad", "فایل CAD"),
    ("bim", "مدل BIM/Revit"),
    ("manual", "دفترچه نصب و راه‌اندازی"),
    ("cert", "گواهی/تست کارخانه"),
    ("price", "لیست قیمت"),
    ("other", "سایر"),
]

RELATION_KINDS = [
    ("compatible", "سازگار با"),
    ("accessory", "لوازم جانبی"),
    ("substitute", "جایگزین"),
    ("complement", "مکمل/همراه"),
]

SPEC_FIELD_TYPES = [
    ("text", "متن"),
    ("number", "عدد"),
    ("choice", "انتخابی"),
    ("bool", "بله/خیر"),
]


class Category(models.Model):
    """دسته‌بندی چندسطحی محصولات."""

    parent = models.ForeignKey(
        "self", verbose_name="دسته والد", null=True, blank=True,
        on_delete=models.CASCADE, related_name="children",
    )
    name = models.CharField("نام", max_length=120)
    slug = models.SlugField("نامک", max_length=140, blank=True)
    code = models.CharField("کد دسته", max_length=20, blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)
    is_featured = models.BooleanField("نمایش در دسته‌های منتخب", default=False)
    icon = models.CharField("آیکون", max_length=40, blank=True)
    description = models.TextField("توضیحات", blank=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی محصولات"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return f"{self.parent.name} / {self.name}" if self.parent_id else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:140]
        return super().save(*args, **kwargs)

    @property
    def full_path(self) -> str:
        parts, node = [], self
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return " / ".join(reversed(parts))


class Brand(models.Model):
    """برند سازنده (موتور، کمپرسور، برند اصلی دستگاه)."""

    name = models.CharField("نام برند", max_length=100, unique=True)
    name_en = models.CharField("نام لاتین", max_length=100, blank=True)
    country = models.CharField("کشور", max_length=60, blank=True)
    is_internal_engine_brand = models.BooleanField("برند موتور/کمپرسور", default=False)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SpecTemplate(models.Model):
    """قالب مشخصات فنی مخصوص هر خانواده کالا.

    ساختار fields: [{"key": "capacity", "label": "ظرفیت سرمایش", "unit": "TR",
                     "type": "number", "choices": [], "required": true}]
    """

    name = models.CharField("نام قالب", max_length=120)
    category = models.ForeignKey(
        Category, verbose_name="دسته‌بندی", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="spec_templates",
    )
    fields = models.JSONField("فیلدهای مشخصات", default=list, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    note = models.CharField("یادداشت", max_length=255, blank=True)

    class Meta:
        verbose_name = "قالب مشخصات فنی"
        verbose_name_plural = "قالب‌های مشخصات فنی"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def field_count(self) -> int:
        return len(self.fields or [])

    def keys(self) -> list[str]:
        return [f.get("key") for f in (self.fields or []) if f.get("key")]


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_stock(self):
        return self.prefetch_related("stock_items__warehouse")


class Product(models.Model):
    """محصول صنعتی با مشخصات فنی ساختاریافته، واحد اندازه‌گیری و قواعد فروش."""

    code = models.CharField("کد کالا", max_length=40, unique=True)
    name = models.CharField("نام کالا", max_length=200)
    name_en = models.CharField("نام لاتین", max_length=200, blank=True)
    slug = models.SlugField("نامک", max_length=220, blank=True)
    model_number = models.CharField("مدل/شماره فنی", max_length=80, blank=True)

    category = models.ForeignKey(
        Category, verbose_name="دسته‌بندی", on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(
        Brand, verbose_name="برند", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="products")
    spec_template = models.ForeignKey(
        SpecTemplate, verbose_name="قالب مشخصات فنی", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="products")

    base_price = models.BigIntegerField("قیمت پایه (تومان)", default=0,
                                        help_text="قیمت لیست؛ قیمت مشتریان از سبدهای قیمت خوانده می‌شود.")
    uom = models.CharField("واحد اندازه‌گیری", max_length=12, choices=UOM_CHOICES, default="device")
    alt_uom = models.CharField("واحد فرعی", max_length=12, choices=UOM_CHOICES, blank=True)
    uom_factor = models.DecimalField(
        "ضریب تبدیل واحد", max_digits=10, decimal_places=3, default=1,
        help_text="مثلاً هر شاخه لوله = ۳ متر → 3")

    min_order_qty = models.DecimalField("حداقل سفارش (MOQ)", max_digits=12, decimal_places=2, default=1)
    max_order_qty = models.DecimalField("حداکثر سفارش", max_digits=12, decimal_places=2, default=0,
                                        help_text="۰ = بدون محدودیت")
    packaging_multiple = models.DecimalField("مضرب بسته‌بندی", max_digits=12, decimal_places=2, default=1)
    lead_time_days = models.PositiveIntegerField("زمان تأمین (روز)", default=0)
    warranty_months = models.PositiveIntegerField("گارانتی (ماه)", default=12)

    availability = models.CharField("وضعیت کالا", max_length=20, choices=AVAILABILITY_CHOICES,
                                    default="in_stock", db_index=True)
    specs = models.JSONField("مشخصات فنی", default=dict, blank=True)
    short_description = models.TextField("توضیح کوتاه", blank=True)
    description = models.TextField("توضیحات کامل", blank=True)

    weight_kg = models.DecimalField("وزن (کیلوگرم)", max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField("ابعاد (mm)", max_length=120, blank=True)
    origin_country = models.CharField("کشور سازنده", max_length=60, blank=True)
    unspsc_code = models.CharField("کد UNSPSC", max_length=20, blank=True)
    hs_code = models.CharField("کد گمرکی (HS)", max_length=20, blank=True)
    tags = models.CharField("برچسب‌ها", max_length=255, blank=True)

    substitute = models.ForeignKey(
        "self", verbose_name="محصول جایگزین", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="replaces")

    is_active = models.BooleanField("فعال", default=True, db_index=True)
    is_featured = models.BooleanField("ویژه", default=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="products_created")

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code or self.name, allow_unicode=True)[:220]
        return super().save(*args, **kwargs)

    @property
    def availability_color(self) -> str:
        return {
            "in_stock": OK, "ready": OK, "made_to_order": WARN,
            "used": INFO, "needs_quote": WARN, "discontinued": DANGER,
        }.get(self.availability, MUTED)

    @property
    def free_qty(self) -> float:
        return sum(item.free_qty for item in self.stock_items.all())

    @property
    def on_hand_qty(self) -> float:
        return sum(float(item.on_hand) for item in self.stock_items.all())

    @property
    def incoming_qty(self) -> float:
        return sum(float(item.incoming) for item in self.stock_items.all())

    @property
    def reorder_point(self) -> float:
        points = [float(item.reorder_point) for item in self.stock_items.all()]
        return max(points) if points else 0

    @property
    def stock_status(self) -> tuple[str, str, str]:
        """(کلید، عنوان، رنگ) وضعیت موجودی برای نمایش در پنل."""
        if not self.stock_items.exists():
            return "none", "بدون رکورد انبار", MUTED
        free = self.free_qty
        if free <= 0:
            return "out", "ناموجود", DANGER
        if free <= self.reorder_point:
            return "low", "زیر نقطه سفارش", WARN
        return "ok", "متعادل", OK

    def apply_packaging(self, qty: float) -> float:
        """گرد کردن تعداد به مضرب بسته‌بندی."""
        multiple = float(self.packaging_multiple or 1)
        if multiple <= 1:
            return qty
        import math

        return math.ceil(qty / multiple) * multiple

    def validate_qty(self, qty: float) -> str | None:
        """اعتبارسنجی تعداد؛ خطا را به‌صورت متن برمی‌گرداند."""
        if qty < float(self.min_order_qty):
            return f"حداقل سفارش {self.min_order_qty} {self.get_uom_display()} است."
        if self.max_order_qty and qty > float(self.max_order_qty):
            return f"حداکثر سفارش {self.max_order_qty} {self.get_uom_display()} است."
        return None

    def get_absolute_url(self):
        """نشانی صفحهٔ کالا در سایت مشتری."""
        from django.urls import reverse

        return reverse("shop:product", kwargs={"slug": self.slug})

    def get_admin_url(self):
        return reverse("admin:catalog_product_change", args=[self.pk])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="images")
    image = models.ImageField("تصویر", upload_to="products/", blank=True, null=True)
    alt = models.CharField("متن جایگزین", max_length=150, blank=True)
    is_main = models.BooleanField("تصویر اصلی", default=False)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.alt or f"تصویر {self.product.code}"


class ProductDocument(models.Model):
    """اسناد فنی نسخه‌دار: دیتاشیت، نقشه، CAD/BIM، گواهی."""

    product = models.ForeignKey(Product, verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="documents")
    kind = models.CharField("نوع سند", max_length=15, choices=DOCUMENT_KINDS, default="datasheet")
    title = models.CharField("عنوان", max_length=180)
    file = models.FileField("فایل", upload_to="documents/", blank=True, null=True)
    external_url = models.URLField("لینک خارجی", blank=True)
    version = models.CharField("نسخه", max_length=20, default="1")
    is_latest = models.BooleanField("آخرین نسخه", default=True)
    reviewed_at = models.DateField("تاریخ آخرین بازبینی", null=True, blank=True)
    approved_by = models.CharField("تأییدکننده فنی", max_length=100, blank=True)
    note = models.CharField("یادداشت", max_length=255, blank=True)
    uploaded_at = models.DateTimeField("زمان بارگذاری", auto_now_add=True)

    class Meta:
        verbose_name = "سند فنی"
        verbose_name_plural = "اسناد و مدارک محصول"
        ordering = ["product", "kind", "-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.product.code} — {self.get_kind_display()} v{self.version}"

    @property
    def kind_color(self) -> str:
        return {
            "datasheet": DANGER, "drawing": INFO, "cad": INFO,
            "bim": VIOLET, "manual": MUTED, "cert": OK,
            "price": ACCENT,
        }.get(self.kind, MUTED)


class ProductRelation(models.Model):
    """سازگاری، لوازم جانبی، مکمل و جایگزین."""

    product = models.ForeignKey(Product, verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="relations")
    target = models.ForeignKey(Product, verbose_name="محصول مرتبط", on_delete=models.CASCADE,
                               related_name="related_to")
    kind = models.CharField("نوع رابطه", max_length=15, choices=RELATION_KINDS, default="compatible")
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "رابطه محصول"
        verbose_name_plural = "سازگاری و لوازم جانبی"
        unique_together = ("product", "target", "kind")

    def __str__(self) -> str:
        return f"{self.product.code} {self.get_kind_display()} {self.target.code}"
