"""انبار: انبار، موجودی، رسید/حواله، درخواست خرید."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.palette import ACCENT, DANGER, INFO, MUTED, OK, VIOLET, WARN

WAREHOUSE_KINDS = [
    ("central", "انبار مرکزی"),
    ("workshop", "انبار کارگاه"),
    ("site", "انبار پای کار"),
    ("consignment", "امانی/نزد مشتری"),
]

MOVE_KINDS = [
    ("receipt", "رسید ورود"),
    ("issue", "حواله خروج"),
    ("reserve", "رزرو سفارش"),
    ("release", "آزادسازی رزرو"),
    ("adjust", "اصلاح موجودی"),
    ("transfer", "انتقال بین انبار"),
    ("return", "برگشت از مشتری"),
]


class Warehouse(models.Model):
    name = models.CharField("نام انبار", max_length=100)
    code = models.CharField("کد انبار", max_length=20, unique=True)
    kind = models.CharField("نوع", max_length=15, choices=WAREHOUSE_KINDS, default="central")
    address = models.CharField("نشانی", max_length=255, blank=True)
    keeper = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="انباردار", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="warehouses")
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "انبار"
        verbose_name_plural = "انبارها"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def stock_value(self) -> int:
        return sum(int(float(item.on_hand) * (item.product.base_price or 0))
                   for item in self.stock_items.select_related("product"))


class StockItem(models.Model):
    """موجودی یک کالا در یک انبار (ATP = موجودی آزاد)."""

    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.CASCADE,
                                related_name="stock_items")
    warehouse = models.ForeignKey(Warehouse, verbose_name="انبار", on_delete=models.CASCADE,
                                  related_name="stock_items")
    on_hand = models.DecimalField("موجودی فیزیکی", max_digits=14, decimal_places=3, default=0)
    reserved = models.DecimalField("رزرو‌شده", max_digits=14, decimal_places=3, default=0)
    incoming = models.DecimalField("در راه (خرید)", max_digits=14, decimal_places=3, default=0)
    min_level = models.DecimalField("حد بحرانی", max_digits=14, decimal_places=3, default=0)
    reorder_point = models.DecimalField("نقطه سفارش", max_digits=14, decimal_places=3, default=0)
    bin_location = models.CharField("موقعیت قفسه", max_length=40, blank=True)
    last_stocktake = models.DateField("آخرین انبارگردانی", null=True, blank=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        verbose_name = "موجودی"
        verbose_name_plural = "موجودی انبارها"
        unique_together = ("product", "warehouse")
        ordering = ["product__code", "warehouse__code"]

    def __str__(self) -> str:
        return f"{self.product.code} @ {self.warehouse.code}"

    @property
    def free_qty(self) -> float:
        return float(self.on_hand) - float(self.reserved)

    @property
    def available_with_incoming(self) -> float:
        return self.free_qty + float(self.incoming)

    @property
    def status(self) -> tuple[str, str, str]:
        """(کلید، برچسب، رنگ)"""
        free = self.free_qty
        if free < 0:
            return "error", "کسری رزرو", DANGER
        if free <= 0:
            return "out", "ناموجود", DANGER
        if float(self.min_level) and free <= float(self.min_level):
            return "critical", "بحرانی", DANGER
        if float(self.reorder_point) and free <= float(self.reorder_point):
            return "low", "زیر نقطه سفارش", WARN
        return "ok", "متعادل", OK

    @property
    def shortage_to_reorder(self) -> float:
        """مقدار لازم برای رسیدن به نقطه سفارش."""
        return max(float(self.reorder_point) + float(self.reserved) - float(self.on_hand), 0)

    @property
    def unit_cost(self) -> int:
        return int(self.product.base_price or 0)

    @property
    def stock_value(self) -> int:
        return int(float(self.on_hand) * self.unit_cost)


class StockMove(models.Model):
    """رسید، حواله، رزرو، اصلاح و انتقال — تاریخچه‌ی کامل تغییرات موجودی."""

    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.PROTECT,
                                related_name="stock_moves")
    warehouse = models.ForeignKey(Warehouse, verbose_name="انبار", on_delete=models.PROTECT,
                                  related_name="stock_moves")
    kind = models.CharField("نوع تراکنش", max_length=10, choices=MOVE_KINDS, db_index=True)
    qty = models.DecimalField("مقدار", max_digits=14, decimal_places=3)
    unit_cost = models.BigIntegerField("بهای واحد (تومان)", default=0)
    reference = models.CharField("مستند/شماره", max_length=60, blank=True)
    order = models.ForeignKey("orders.Order", verbose_name="سفارش", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="stock_moves")
    counterparty = models.CharField("طرف حساب", max_length=120, blank=True)
    note = models.CharField("توضیح", max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="stock_moves")
    created_at = models.DateTimeField("زمان", default=timezone.now, db_index=True)
    occurred_on = models.DateField("تاریخ سند", default=timezone.localdate)

    class Meta:
        verbose_name = "تراکنش انبار"
        verbose_name_plural = "رسیدها و حواله‌ها"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.product.code} × {self.qty}"

    @property
    def signed_qty(self) -> Decimal:
        qty = Decimal(self.qty)
        return -qty if self.kind in ("issue", "reserve") else qty

    @property
    def kind_color(self) -> str:
        return {
            "receipt": OK, "issue": DANGER, "reserve": WARN,
            "release": ACCENT, "adjust": VIOLET, "transfer": INFO,
            "return": WARN,
        }.get(self.kind, MUTED)


class PurchaseRequest(models.Model):
    """درخواست خرید کالای کم‌موجود / ساخت به سفارش."""

    STATUS = [
        ("draft", "پیش‌نویس"),
        ("submitted", "ثبت‌شده"),
        ("approved", "تأییدشده"),
        ("ordered", "سفارش خرید صادر شد"),
        ("received", "دریافت شد"),
        ("cancelled", "لغو‌شده"),
    ]

    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.PROTECT,
                                related_name="purchase_requests")
    warehouse = models.ForeignKey(Warehouse, verbose_name="انبار مقصد", on_delete=models.PROTECT,
                                  related_name="purchase_requests")
    qty = models.DecimalField("مقدار درخواستی", max_digits=14, decimal_places=3)
    status = models.CharField("وضعیت", max_length=12, choices=STATUS, default="draft", db_index=True)
    needed_by = models.DateField("مورد نیاز تا", null=True, blank=True)
    supplier = models.CharField("تأمین‌کننده", max_length=120, blank=True)
    estimated_cost = models.BigIntegerField("برآورد هزینه (تومان)", default=0)
    note = models.CharField("توضیح", max_length=255, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="درخواست‌کننده", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="purchase_requests")
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)

    class Meta:
        verbose_name = "درخواست خرید"
        verbose_name_plural = "درخواست‌های خرید"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PR-{self.pk} {self.product.code} × {self.qty}"

    @property
    def status_color(self) -> str:
        return {
            "draft": MUTED, "submitted": INFO, "approved": OK,
            "ordered": ACCENT, "received": OK, "cancelled": DANGER,
        }.get(self.status, MUTED)
