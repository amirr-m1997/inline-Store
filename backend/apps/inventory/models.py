from decimal import Decimal
from decimal import ROUND_CEILING

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from apps.catalog.models import Product

class Inventory(models.Model):
    product = models.OneToOneField(Product, related_name="inventory", on_delete=models.CASCADE)
    on_hand_quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0, validators=[MinValueValidator(Decimal("0"))])
    reserved_quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0, validators=[MinValueValidator(Decimal("0"))])
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(on_hand_quantity__gte=0), name="inventory_on_hand_nonnegative"), models.CheckConstraint(check=models.Q(reserved_quantity__gte=0), name="inventory_reserved_nonnegative"), models.CheckConstraint(check=models.Q(reserved_quantity__lte=models.F("on_hand_quantity")), name="inventory_reserved_lte_on_hand")]
        verbose_name = "موجودی انبار"
        verbose_name_plural = "موجودی‌های انبار"
    @property
    def available_quantity(self): return self.on_hand_quantity - self.reserved_quantity
    @classmethod
    def reserve(cls, product_id, quantity):
        with transaction.atomic():
            inventory = cls.objects.select_for_update().get(product_id=product_id)
            if quantity <= 0 or inventory.available_quantity < quantity: raise ValueError("Insufficient available inventory")
            inventory.reserved_quantity = models.F("reserved_quantity") + quantity
            inventory.save(update_fields=("reserved_quantity", "updated_at"))
            return inventory

    @classmethod
    def release(cls, product_id, quantity):
        with transaction.atomic():
            inventory = cls.objects.select_for_update().get(product_id=product_id)
            if quantity <= 0 or inventory.reserved_quantity < quantity:
                raise ValueError("Cannot release more inventory than is reserved")
            inventory.reserved_quantity = models.F("reserved_quantity") - quantity
            inventory.save(update_fields=("reserved_quantity", "updated_at"))
            return inventory
    def __str__(self): return str(self.product)


class ReplenishmentRule(models.Model):
    """Per-product replenishment policy, reviewed from the operations dashboard."""

    product = models.OneToOneField(Product, related_name="replenishment_rule", on_delete=models.CASCADE)
    minimum_quantity = models.DecimalField(
        "حداقل موجودی قابل‌قبول", max_digits=18, decimal_places=6, default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    maximum_quantity = models.DecimalField(
        "سقف هدف موجودی", max_digits=18, decimal_places=6, default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    order_multiple = models.DecimalField(
        "مضرب سفارش", max_digits=18, decimal_places=6, default=1,
        validators=[MinValueValidator(Decimal("0.000001"))],
    )
    lead_time_days = models.PositiveIntegerField("زمان تأمین (روز)", default=0)
    is_auto = models.BooleanField("ایجاد خودکار درخواست تأمین", default=False)
    is_active = models.BooleanField("فعال", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(maximum_quantity__gte=models.F("minimum_quantity")),
                name="replenishment_max_gte_min",
            ),
        ]
        verbose_name = "قانون تأمین مجدد"
        verbose_name_plural = "قوانین تأمین مجدد"

    @property
    def available_quantity(self):
        inventory = getattr(self.product, "inventory", None)
        return inventory.available_quantity if inventory else Decimal("0")

    @property
    def suggested_order_quantity(self):
        needed = max(Decimal("0"), self.maximum_quantity - self.available_quantity)
        if not needed:
            return Decimal("0")
        multiple = self.order_multiple or Decimal("1")
        return (needed / multiple).to_integral_value(rounding=ROUND_CEILING) * multiple

    def __str__(self):
        return f"{self.product.code} — تأمین تا {self.maximum_quantity}"

class Receipt(models.Model):
    product = models.ForeignKey(Product, related_name="receipts", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    occurred_at = models.DateTimeField()
    reference = models.CharField(max_length=128, blank=True)
    unit_purchase_price_irr = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    usd_rate = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-occurred_at",)
        verbose_name = "رسید انبار"
        verbose_name_plural = "رسیدهای انبار"

class Issue(models.Model):
    product = models.ForeignKey(Product, related_name="issues", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    occurred_at = models.DateTimeField()
    reference = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-occurred_at",)
        verbose_name = "حواله خروج"
        verbose_name_plural = "حواله‌های خروج"

class Reservation(models.Model):
    class Status(models.TextChoices): ACTIVE = "active", "فعال"; RELEASED = "released", "آزادشده"; CONVERTED = "converted", "تبدیل‌شده"; EXPIRED = "expired", "منقضی‌شده"
    product = models.ForeignKey(Product, related_name="reservations", on_delete=models.PROTECT)
    cart_item = models.ForeignKey("carts.CartItem", null=True, blank=True, related_name="reservations", on_delete=models.SET_NULL)
    order_item = models.ForeignKey("orders.OrderItem", null=True, blank=True, related_name="reservations", on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=("product", "status", "expires_at"))]
        verbose_name = "رزرو موجودی"
        verbose_name_plural = "رزروهای موجودی"
