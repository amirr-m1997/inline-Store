import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def generate_order_number():
    return f"ORD-{uuid.uuid4().hex[:16].upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "در انتظار پرداخت"
        PROCESSING = "processing", "در حال پردازش"
        CONFIRMED = "confirmed", "تأیید شده"
        PREPARING = "preparing", "در حال آماده‌سازی"
        SHIPPED = "shipped", "ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده"
        CANCELLED = "cancelled", "لغوشده"
        RETURNED = "returned", "مرجوع شده"

    order_number = models.CharField("شماره سفارش", max_length=32, unique=True, default=generate_order_number, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="orders", on_delete=models.SET_NULL)
    source_cart = models.OneToOneField("carts.Cart", null=True, blank=True, related_name="order", on_delete=models.PROTECT)
    status = models.CharField("وضعیت", max_length=24, choices=Status.choices, default=Status.PENDING_PAYMENT, db_index=True)
    currency = models.CharField("ارز", max_length=3, default="IRR")
    subtotal = models.DecimalField("جمع اقلام", max_digits=18, decimal_places=2, default=0)
    discount_code = models.CharField("کد تخفیف", max_length=64, blank=True)
    discount_percentage = models.DecimalField("درصد تخفیف", max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    discount_amount = models.DecimalField("مبلغ تخفیف", max_digits=18, decimal_places=2, default=0)
    shipping_cost = models.DecimalField("هزینه ارسال", max_digits=18, decimal_places=2, default=0)
    final_amount = models.DecimalField("مبلغ نهایی", max_digits=18, decimal_places=2, default=0)
    customer_first_name = models.CharField("نام مشتری", max_length=150, blank=True)
    customer_last_name = models.CharField("نام خانوادگی مشتری", max_length=150, blank=True)
    customer_email = models.EmailField("ایمیل مشتری", blank=True)
    customer_phone = models.CharField("تلفن مشتری", max_length=32, blank=True)
    customer_company_name = models.CharField("نام شرکت", max_length=255, blank=True)
    customer_national_id = models.CharField("شناسه ملی", max_length=32, blank=True)
    shipping_province = models.CharField("استان تحویل", max_length=100, blank=True)
    shipping_city = models.CharField("شهر تحویل", max_length=100, blank=True)
    shipping_postal_code = models.CharField("کدپستی تحویل", max_length=20, blank=True)
    shipping_address = models.TextField("نشانی تحویل", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)
    shipped_at = models.DateTimeField("زمان ارسال", null=True, blank=True)
    delivered_at = models.DateTimeField("زمان تحویل", null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("customer", "status", "-created_at"))]
        constraints = [
            models.CheckConstraint(check=models.Q(subtotal__gte=0), name="order_subtotal_nonnegative"),
            models.CheckConstraint(check=models.Q(discount_amount__gte=0), name="order_discount_nonnegative"),
            models.CheckConstraint(check=models.Q(shipping_cost__gte=0), name="order_shipping_nonnegative"),
            models.CheckConstraint(check=models.Q(final_amount__gte=0), name="order_final_nonnegative"),
        ]
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"

    def save(self, *args, **kwargs):
        previous = None if self._state.adding else Order.objects.filter(pk=self.pk).values_list("status", flat=True).first()
        now = timezone.now()
        timestamp_fields = []
        if self.status == self.Status.SHIPPED and not self.shipped_at:
            self.shipped_at = now; timestamp_fields.append("shipped_at")
        if self.status == self.Status.DELIVERED and not self.delivered_at:
            self.delivered_at = now; timestamp_fields.append("delivered_at")
        if timestamp_fields and kwargs.get("update_fields"):
            kwargs["update_fields"] = tuple(set(kwargs["update_fields"]) | set(timestamp_fields))
        super().save(*args, **kwargs)
        if previous != self.status:
            OrderStatusHistory.objects.create(order=self, status=self.status, description=self.get_status_display())

    def __str__(self): return self.order_number


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name="status_history", on_delete=models.CASCADE)
    status = models.CharField("وضعیت", max_length=24, choices=Order.Status.choices)
    description = models.CharField("توضیحات", max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "تاریخچه وضعیت سفارش"
        verbose_name_plural = "تاریخچه وضعیت سفارش‌ها"

    def __str__(self): return f"{self.order.order_number} — {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", null=True, blank=True, related_name="order_items", on_delete=models.SET_NULL)
    product_name = models.CharField("نام محصول در زمان خرید", max_length=255)
    product_code = models.CharField("کد محصول در زمان خرید", max_length=64)
    unit = models.CharField("واحد در زمان خرید", max_length=64, blank=True)
    unit_price = models.DecimalField("قیمت واحد در زمان خرید", max_digits=18, decimal_places=2)
    quantity = models.PositiveIntegerField("تعداد", validators=[MinValueValidator(1)])
    discount_percentage = models.DecimalField("درصد تخفیف قلم", max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    discount_amount = models.DecimalField("مبلغ تخفیف قلم", max_digits=18, decimal_places=2, default=0)
    line_subtotal = models.DecimalField("جمع قبل از تخفیف", max_digits=18, decimal_places=2)
    line_total = models.DecimalField("جمع نهایی قلم", max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(check=models.Q(unit_price__gte=0), name="orderitem_price_nonnegative"),
            models.CheckConstraint(check=models.Q(discount_amount__gte=0), name="orderitem_discount_nonnegative"),
            models.CheckConstraint(check=models.Q(line_subtotal__gte=0), name="orderitem_subtotal_nonnegative"),
            models.CheckConstraint(check=models.Q(line_total__gte=0), name="orderitem_total_nonnegative"),
        ]
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"

    def __str__(self): return f"{self.order.order_number} — {self.product_code}"


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "ایجادشده"
        PENDING = "pending", "در انتظار پرداخت"
        VERIFIED = "verified", "تأییدشده"
        FAILED = "failed", "ناموفق"
        CANCELLED = "cancelled", "لغوشده"
        REFUNDED = "refunded", "بازپرداخت‌شده"

    order = models.ForeignKey(Order, related_name="payments", on_delete=models.PROTECT)
    gateway = models.CharField("درگاه", max_length=32, default="zarinpal", db_index=True)
    amount = models.DecimalField("مبلغ", max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    authority = models.CharField("Authority", max_length=128, blank=True, db_index=True)
    reference_id = models.CharField("شماره مرجع", max_length=128, blank=True, db_index=True)
    status = models.CharField("وضعیت", max_length=16, choices=Status.choices, default=Status.CREATED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("gateway", "authority"), condition=~models.Q(authority=""), name="payment_gateway_authority_unique"),
            models.UniqueConstraint(fields=("gateway", "reference_id"), condition=~models.Q(reference_id=""), name="payment_gateway_reference_unique"),
        ]
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self): return f"{self.order.order_number} — {self.gateway} — {self.status}"


class Invoice(models.Model):
    order = models.OneToOneField(Order, related_name="invoice", on_delete=models.PROTECT)
    invoice_number = models.CharField("شماره فاکتور", max_length=64, unique=True)
    company_name = models.CharField("نام شرکت", max_length=255, blank=True)
    customer_name = models.CharField("نام مشتری", max_length=255)
    national_id = models.CharField("شناسه ملی", max_length=32, blank=True)
    economic_code = models.CharField("کد اقتصادی", max_length=32, blank=True)
    phone = models.CharField("تلفن", max_length=32, blank=True)
    address = models.TextField("نشانی", blank=True)
    items_snapshot = models.JSONField("تصویر ثابت اقلام", default=list)
    subtotal = models.DecimalField("جمع اقلام", max_digits=18, decimal_places=2)
    tax = models.DecimalField("مالیات", max_digits=18, decimal_places=2, default=0)
    discount = models.DecimalField("تخفیف", max_digits=18, decimal_places=2, default=0)
    final_amount = models.DecimalField("مبلغ نهایی", max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField("فایل PDF", upload_to="invoices/%Y/%m/", blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"

    def __str__(self): return self.invoice_number


class InvoiceEmailLog(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="email_logs", on_delete=models.CASCADE)
    recipient = models.EmailField("گیرنده")
    success = models.BooleanField("موفق", default=False)
    error_message = models.TextField("خطا", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "گزارش ارسال فاکتور"
        verbose_name_plural = "گزارش‌های ارسال فاکتور"


class ProformaRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "ثبت شده"
        REVIEWING = "reviewing", "در حال بررسی"
        ISSUED = "issued", "صادر شده"
        REJECTED = "rejected", "رد شده"

    order = models.OneToOneField(Order, related_name="proforma_request", on_delete=models.PROTECT)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="proforma_requests", on_delete=models.PROTECT)
    status = models.CharField("وضعیت", max_length=16, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    customer_note = models.TextField("توضیحات مشتری", blank=True)
    admin_note = models.TextField("توضیحات مدیر", blank=True)
    requested_at = models.DateTimeField("زمان درخواست", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-requested_at",)
        verbose_name = "درخواست پیش‌فاکتور رسمی"
        verbose_name_plural = "درخواست‌های پیش‌فاکتور رسمی"

    def __str__(self): return f"{self.order.order_number} — {self.get_status_display()}"
