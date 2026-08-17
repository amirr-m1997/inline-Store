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
