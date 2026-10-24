from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.catalog.models import Product
class Currency(models.TextChoices): IRR = "IRR", "ریال ایران"; USD = "USD", "دلار آمریکا"
class ProductPrice(models.Model):
    product = models.ForeignKey(Product, related_name="prices", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [models.Index(fields=("product", "effective_from"))]
        verbose_name = "قیمت محصول"
        verbose_name_plural = "قیمت محصولات"
class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3, choices=Currency.choices)
    rate_to_irr = models.DecimalField(max_digits=18, decimal_places=4)
    rate_date = models.DateField()
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("currency", "rate_date"), name="currency_rate_per_date_unique")]
        verbose_name = "نرخ ارز"
        verbose_name_plural = "نرخ‌های ارز"


class CustomerPriceList(models.Model):
    """A time-bounded commercial agreement for one authenticated customer."""

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="customer_price_lists",
        on_delete=models.CASCADE,
        verbose_name="مشتری / شرکت",
    )
    name = models.CharField("نام قرارداد قیمت", max_length=180)
    currency = models.CharField("ارز", max_length=3, choices=Currency.choices, default=Currency.IRR)
    priority = models.PositiveSmallIntegerField("اولویت", default=100)
    valid_from = models.DateTimeField("شروع اعتبار")
    valid_until = models.DateTimeField("پایان اعتبار", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    note = models.TextField("یادداشت داخلی", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-priority", "name", "-created_at")
        indexes = [
            models.Index(fields=("customer", "is_active", "valid_from"), name="price_list_customer_active_idx"),
        ]
        verbose_name = "فهرست قیمت سازمانی"
        verbose_name_plural = "فهرست‌های قیمت سازمانی"

    def clean(self):
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": "پایان اعتبار نمی‌تواند قبل از شروع باشد."})

    def __str__(self):
        return f"{self.customer.company_name or self.customer} — {self.name}"


class CustomerPriceListItem(models.Model):
    """A quantity tier: fixed price wins, otherwise percentage applies to catalog price."""

    price_list = models.ForeignKey(
        CustomerPriceList,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="فهرست قیمت",
    )
    product = models.ForeignKey(Product, related_name="customer_price_items", on_delete=models.CASCADE)
    minimum_quantity = models.PositiveIntegerField(
        "حداقل تعداد", default=1, validators=[MinValueValidator(1)],
    )
    fixed_amount = models.DecimalField(
        "قیمت توافقی ثابت", max_digits=18, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    discount_percentage = models.DecimalField(
        "تخفیف از قیمت عمومی", max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("price_list", "product", "minimum_quantity")
        constraints = [
            models.UniqueConstraint(
                fields=("price_list", "product", "minimum_quantity"),
                name="customer_price_tier_unique",
            ),
        ]
        verbose_name = "قلم قیمت سازمانی"
        verbose_name_plural = "اقلام قیمت سازمانی"

    def clean(self):
        if self.fixed_amount is None and not self.discount_percentage:
            raise ValidationError("برای هر قلم، قیمت ثابت یا درصد تخفیف را وارد کنید.")

    def __str__(self):
        return f"{self.price_list} — {self.product.code} × {self.minimum_quantity}"
