import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.core.validators import MaxValueValidator
from apps.catalog.models import Product
class DiscountCode(models.Model):
    code = models.CharField("کد تخفیف", max_length=64, unique=True)
    percentage = models.DecimalField("درصد تخفیف", max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01), MaxValueValidator(100)])
    minimum_order_amount = models.DecimalField("حداقل مبلغ سفارش (ریال)", max_digits=18, decimal_places=2, default=0)
    valid_from = models.DateTimeField("شروع اعتبار")
    valid_until = models.DateTimeField("پایان اعتبار", null=True, blank=True)
    max_uses = models.PositiveIntegerField("حداکثر دفعات استفاده", null=True, blank=True)
    usage_count = models.PositiveIntegerField("دفعات استفاده‌شده", default=0, editable=False)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.code} — {self.percentage}%"


class Cart(models.Model):
    class Status(models.TextChoices): ACTIVE = "active", "فعال"; CHECKED_OUT = "checked_out", "تسویه‌شده"; ABANDONED = "abandoned", "رهاشده"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="carts", on_delete=models.CASCADE)
    guest_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    discount_code = models.ForeignKey(DiscountCode, null=True, blank=True, related_name="carts", on_delete=models.SET_NULL)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    customer_first_name = models.CharField(max_length=150, blank=True)
    customer_last_name = models.CharField(max_length=150, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=32, blank=True)
    customer_company_name = models.CharField(max_length=255, blank=True)
    customer_national_id = models.CharField(max_length=32, blank=True)
    shipping_province = models.CharField(max_length=100, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("cart", "product"), name="cart_product_unique")]
        verbose_name = "آیتم سبد خرید"
        verbose_name_plural = "آیتم‌های سبد خرید"
