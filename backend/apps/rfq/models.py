import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Product


def rfq_reference():
    return f"RFQ-{uuid.uuid4().hex[:10].upper()}"


class RequestForQuotation(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "ثبت شده"
        UNDER_REVIEW = "under_review", "در حال بررسی"
        QUOTED = "quoted", "قیمت‌گذاری شده"
        CLOSED = "closed", "بسته شده"
        CANCELLED = "cancelled", "لغوشده"

    reference = models.CharField("شناسه استعلام", max_length=24, unique=True, default=rfq_reference, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="rfq_requests", on_delete=models.SET_NULL)
    company_name = models.CharField("نام شرکت", max_length=255, blank=True)
    contact_name = models.CharField("نام تماس", max_length=255)
    phone = models.CharField("تلفن", max_length=64, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    subject = models.CharField("موضوع", max_length=255, blank=True)
    message = models.TextField("شرح نیاز", max_length=5000, blank=True)
    preferred_contact_method = models.CharField("روش تماس ترجیحی", max_length=24, blank=True)
    source = models.CharField("منبع", max_length=64, default="website")
    status = models.CharField("وضعیت", max_length=24, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    internal_notes = models.TextField("یادداشت داخلی", max_length=5000, blank=True)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("customer", "created_at"), name="rfq_customer_created_idx"), models.Index(fields=("status", "created_at"), name="rfq_status_created_idx")]
        verbose_name = "استعلام قیمت"
        verbose_name_plural = "استعلام‌های قیمت"

    def clean(self):
        if not (self.phone or self.email):
            raise ValidationError("حداقل یکی از تلفن یا ایمیل باید وارد شود.")

    def __str__(self):
        return f"{self.reference} — {self.contact_name}"


class RequestForQuotationItem(models.Model):
    rfq = models.ForeignKey(RequestForQuotation, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", related_name="rfq_items", on_delete=models.PROTECT)
    requested_quantity = models.PositiveIntegerField("تعداد درخواستی", validators=[MinValueValidator(1)])
    customer_note = models.CharField("یادداشت مشتری", max_length=1000, blank=True)
    product_code_snapshot = models.CharField("کد محصول در زمان ثبت", max_length=64)
    product_name_snapshot = models.CharField("نام محصول در زمان ثبت", max_length=255)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    class Meta:
        ordering = ("id",)
        constraints = [models.UniqueConstraint(fields=("rfq", "product"), name="rfq_product_unique")]
        verbose_name = "قلم استعلام قیمت"
        verbose_name_plural = "اقلام استعلام قیمت"

    def clean(self):
        if self.product_id and not Product.objects.filter(pk=self.product_id, is_active=True).exists():
            raise ValidationError({"product": "این محصول برای استعلام عمومی فعال نیست."})

    def __str__(self):
        return f"{self.rfq.reference} — {self.product_code_snapshot}"


def quotation_reference():
    return f"QT-{uuid.uuid4().hex[:10].upper()}"


class SalesQuotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        ISSUED = "issued", "صادر شده"
        EXPIRED = "expired", "منقضی شده"
        CANCELLED = "cancelled", "لغو شده"

    class Currency(models.TextChoices):
        IRR = "IRR", "ریال ایران"
        USD = "USD", "دلار آمریکا"

    reference = models.CharField("شناسه پیشنهاد قیمت", max_length=24, unique=True, default=quotation_reference, editable=False)
    rfq = models.OneToOneField(RequestForQuotation, related_name="quotation", on_delete=models.PROTECT)
    status = models.CharField("وضعیت", max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    currency = models.CharField("ارز", max_length=3, choices=Currency.choices, blank=True)
    issued_at = models.DateTimeField("زمان صدور", null=True, blank=True)
    expires_at = models.DateTimeField("زمان انقضا", null=True, blank=True)
    public_note = models.TextField("یادداشت مشتری", max_length=5000, blank=True)
    internal_notes = models.TextField("یادداشت داخلی", max_length=5000, blank=True)
    source = models.CharField("منبع داخلی", max_length=64, default="manual")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="created_sales_quotations", on_delete=models.SET_NULL)
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("status", "created_at"), name="quotation_status_created_idx")]
        verbose_name = "پیشنهاد قیمت"
        verbose_name_plural = "پیشنهادهای قیمت"

    def clean(self):
        if self.expires_at and self.issued_at and self.expires_at < self.issued_at:
            raise ValidationError({"expires_at": "زمان انقضا نمی‌تواند قبل از زمان صدور باشد."})
        if self.status == self.Status.ISSUED:
            if not self.currency:
                raise ValidationError({"currency": "ارز برای پیشنهاد صادرشده الزامی است."})
            if not self.items.exists():
                raise ValidationError("پیشنهاد قیمت باید حداقل یک قلم داشته باشد.")
            if self.items.filter(unit_price__lte=0).exists():
                raise ValidationError("قیمت تمام اقلام پیشنهاد صادرشده باید بزرگ‌تر از صفر باشد.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.filter(pk=self.pk).values("status", "rfq_id", "reference", "currency").first()
            if previous and previous["status"] == self.Status.ISSUED:
                for field in ("rfq_id", "reference", "currency", "status"):
                    if getattr(self, field) != previous[field]:
                        raise ValidationError("پیشنهاد صادرشده قابل تغییر تجاری نیست.")
        if self.status == self.Status.ISSUED and not self.issued_at:
            from django.utils import timezone
            self.issued_at = timezone.now()
        super().save(*args, **kwargs)
        if self.status == self.Status.ISSUED:
            RequestForQuotation.objects.filter(pk=self.rfq_id).exclude(status=RequestForQuotation.Status.QUOTED).update(status=RequestForQuotation.Status.QUOTED)

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    def __str__(self):
        return f"{self.reference} — {self.rfq.reference}"


class SalesQuotationItem(models.Model):
    quotation = models.ForeignKey(SalesQuotation, related_name="items", on_delete=models.CASCADE)
    source_rfq_item = models.ForeignKey(RequestForQuotationItem, null=True, blank=True, related_name="quotation_items", on_delete=models.SET_NULL)
    product = models.ForeignKey("catalog.Product", null=True, blank=True, related_name="quotation_items", on_delete=models.PROTECT)
    product_name_snapshot = models.CharField("نام محصول در زمان صدور", max_length=255)
    product_code_snapshot = models.CharField("کد محصول در زمان صدور", max_length=64)
    quantity = models.PositiveIntegerField("تعداد", validators=[MinValueValidator(1)])
    unit_price = models.DecimalField("قیمت واحد", max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "قلم پیشنهاد قیمت"
        verbose_name_plural = "اقلام پیشنهاد قیمت"

    @property
    def line_total(self):
        if self.unit_price is None or self.quantity is None:
            return Decimal("0.00")
        return self.unit_price * self.quantity

    def clean(self):
        if self.quotation_id and self.quotation.status == SalesQuotation.Status.ISSUED:
            raise ValidationError("اقلام پیشنهاد صادرشده قابل تغییر نیستند.")

    def save(self, *args, **kwargs):
        if type(self).objects.filter(quotation_id=self.quotation_id, quotation__status=SalesQuotation.Status.ISSUED).exclude(pk=self.pk).exists() or (not self._state.adding and type(self).objects.filter(pk=self.pk, quotation__status=SalesQuotation.Status.ISSUED).exists()):
            raise ValidationError("اقلام پیشنهاد صادرشده قابل تغییر نیستند.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quotation.reference} — {self.product_code_snapshot}"


class SalesQuotationResponse(models.Model):
    class ResponseType(models.TextChoices):
        ACCEPTED = "accepted", "تأیید شده"
        REJECTED = "rejected", "رد شده"
        REVISION_REQUESTED = "revision_requested", "درخواست اصلاح"

    quotation = models.OneToOneField(SalesQuotation, related_name="customer_response", on_delete=models.PROTECT)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="quotation_responses")
    response = models.CharField("پاسخ مشتری", max_length=24, choices=ResponseType.choices)
    note = models.TextField("یادداشت مشتری", max_length=2000, blank=True)
    response_at = models.DateTimeField("زمان پاسخ", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-response_at", "-id")
        indexes = [models.Index(fields=("response", "response_at"), name="quote_resp_type_time_idx")]
        verbose_name = "پاسخ مشتری به پیشنهاد"
        verbose_name_plural = "پاسخ‌های مشتری به پیشنهادها"

    def clean(self):
        if self.quotation_id and self.customer_id and self.quotation.rfq.customer_id != self.customer_id:
            raise ValidationError("پاسخ باید توسط مالک پیشنهاد ثبت شود.")
        if self.response == self.ResponseType.REVISION_REQUESTED and not self.note.strip():
            raise ValidationError({"note": "برای درخواست اصلاح، توضیحات الزامی است."})

    def __str__(self):
        return f"{self.quotation.reference} — {self.get_response_display()}"
