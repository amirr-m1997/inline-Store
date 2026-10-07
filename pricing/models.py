"""قیمت‌گذاری B2B: سبد قیمت، قیمت اقلام، قیمت پلکانی حجمی."""
from __future__ import annotations

from django.db import models

LIST_KINDS = [
    ("list", "لیست عمومی"),
    ("partner", "همکار"),
    ("project", "پروژه‌ای"),
    ("contractor", "پیمانکاری"),
    ("export", "صادراتی"),
    ("internal", "داخلی/نمایندگی"),
]


class PriceList(models.Model):
    """سبد قیمت — می‌تواند به یک شرکت، گروه مشتری یا پروژه اختصاص یابد."""

    name = models.CharField("نام سبد", max_length=140)
    code = models.CharField("کد سبد", max_length=30, unique=True)
    kind = models.CharField("نوع", max_length=12, choices=LIST_KINDS, default="list")
    discount_pct = models.DecimalField(
        "درصد تخفیف عمومی", max_digits=5, decimal_places=2, default=0,
        help_text="روی اقلامی که قیمت اختصاصی ندارند اعمال می‌شود.")
    valid_from = models.DateField("اعتبار از", null=True, blank=True)
    valid_until = models.DateField("اعتبار تا", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    note = models.CharField("یادداشت", max_length=255, blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "سبد قیمت"
        verbose_name_plural = "سبدهای قیمت مشتریان"
        ordering = ["-is_active", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        return bool(self.valid_until and self.valid_until < timezone.localdate())

    @property
    def days_to_expiry(self) -> int | None:
        from django.utils import timezone

        if not self.valid_until:
            return None
        return (self.valid_until - timezone.localdate()).days

    @property
    def status_label(self) -> tuple[str, str]:
        if not self.is_active:
            return "غیرفعال", "#64748b"
        if self.is_expired:
            return "منقضی", "#c02626"
        days = self.days_to_expiry
        if days is not None and days <= 14:
            from core.utils import num as _num

            return f"{_num(days, 0)} روز تا انقضا", "#b45309"
        return "فعال", "#12855f"


class PriceListItem(models.Model):
    """قیمت اختصاصی یک کالا در یک سبد قیمت."""

    price_list = models.ForeignKey(PriceList, verbose_name="سبد قیمت", on_delete=models.CASCADE,
                                   related_name="items")
    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="price_items")
    price = models.BigIntegerField("قیمت (تومان)")
    valid_from = models.DateField("اعتبار از", null=True, blank=True)
    valid_until = models.DateField("اعتبار تا", null=True, blank=True)
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "ردیف قیمت"
        verbose_name_plural = "ردیف‌های قیمت"
        unique_together = ("price_list", "product")
        ordering = ["price_list", "product__code"]

    def __str__(self) -> str:
        return f"{self.price_list.code} / {self.product.code}"

    def is_valid_on(self, day=None) -> bool:
        from django.utils import timezone

        day = day or timezone.localdate()
        if self.valid_from and day < self.valid_from:
            return False
        if self.valid_until and day > self.valid_until:
            return False
        return True


class QuantityPriceBreak(models.Model):
    """پله‌های قیمت حجمی/پلکانی برای یک کالا در یک سبد قیمت."""

    price_list = models.ForeignKey(PriceList, verbose_name="سبد قیمت", on_delete=models.CASCADE,
                                   related_name="breaks")
    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="price_breaks")
    min_qty = models.DecimalField("از تعداد", max_digits=12, decimal_places=2)
    discount_pct = models.DecimalField("درصد تخفیف", max_digits=5, decimal_places=2, default=0)
    price = models.BigIntegerField("قیمت واحد (تومان)", null=True, blank=True,
                                   help_text="خالی بگذارید تا از درصد تخفیف محاسبه شود.")
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "قیمت پلکانی"
        verbose_name_plural = "قیمت‌های پلکانی حجمی"
        ordering = ["product", "min_qty"]
        unique_together = ("price_list", "product", "min_qty")

    def __str__(self) -> str:
        return f"{self.product.code} از {self.min_qty}"

    def unit_price(self, base_price: int) -> int:
        if self.price:
            return int(self.price)
        return int(round(base_price * (1 - float(self.discount_pct) / 100)))
