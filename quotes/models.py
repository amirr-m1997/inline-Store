"""استعلام قیمت (RFQ)، ردیف‌های پیشنهاد و گفت‌وگوی مذاکره."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

QUOTE_STATUS = [
    ("new", "جدید"),
    ("tech_review", "بررسی فنی"),
    ("pricing", "قیمت‌گذاری"),
    ("sent", "پیش‌فاکتور ارسال‌شده"),
    ("negotiation", "در مذاکره"),
    ("won", "تأیید مشتری"),
    ("converted", "تبدیل به سفارش"),
    ("lost", "از دست رفته"),
    ("expired", "منقضی"),
]

PRIORITIES = [("urgent", "فوری"), ("normal", "عادی"), ("project", "پروژه‌ای")]


class Quote(models.Model):
    """درخواست استعلام قیمت / پیش‌فاکتور قابل مذاکره."""

    number = models.CharField("شماره استعلام", max_length=25, unique=True, blank=True)
    company = models.ForeignKey("customers.Company", verbose_name="مشتری", on_delete=models.PROTECT,
                                related_name="quotes")
    contact = models.ForeignKey("customers.CompanyUser", verbose_name="کاربر درخواست‌دهنده",
                                null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="quotes")
    project_name = models.CharField("نام پروژه/کاربرد", max_length=160, blank=True)
    status = models.CharField("وضعیت", max_length=12, choices=QUOTE_STATUS, default="new", db_index=True)
    priority = models.CharField("اولویت", max_length=8, choices=PRIORITIES, default="normal", db_index=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="کارشناس فروش", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="assigned_quotes")
    technical_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="کارشناس فنی", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="technical_quotes")

    sla_due_at = models.DateTimeField("مهلت پاسخ (SLA)", null=True, blank=True)
    first_response_at = models.DateTimeField("زمان اولین پاسخ", null=True, blank=True)
    valid_until = models.DateField("اعتبار قیمت تا", null=True, blank=True)

    discount_pct = models.DecimalField("درصد تخفیف کل", max_digits=5, decimal_places=2, default=0)
    payment_terms = models.CharField("شرایط تسویه", max_length=120, blank=True)
    delivery_terms = models.CharField("شرایط تحویل", max_length=120, blank=True)
    delivery_days = models.PositiveIntegerField("زمان تحویل (روز)", default=0)

    customer_note = models.TextField("یادداشت مشتری", blank=True)
    internal_note = models.TextField("یادداشت داخلی (مخفی از مشتری)", blank=True)
    lost_reason = models.CharField("دلیل از دست رفتن", max_length=200, blank=True)

    source = models.CharField("منبع", max_length=20, default="site",
                              choices=[("site", "سایت"), ("panel", "پنل"), ("rep", "نماینده"),
                                       ("phone", "تلفنی"), ("email", "ایمیل")])
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_quotes")
    order = models.ForeignKey("orders.Order", verbose_name="سفارش حاصل", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="source_quotes")

    created_at = models.DateTimeField("تاریخ ثبت", default=timezone.now, db_index=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)
    version = models.PositiveIntegerField("نسخه پیشنهاد", default=1)

    class Meta:
        verbose_name = "استعلام قیمت"
        verbose_name_plural = "استعلام‌های قیمت"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "priority"]),
                   models.Index(fields=["sla_due_at"])]

    def __str__(self) -> str:
        return f"{self.number} — {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.number:
            from django.db.models import Max

            year = timezone.now().astimezone().year - 621  # سال شمسی تقریبی
            last = Quote.objects.filter(number__startswith=f"RFQ-{year}-").aggregate(m=Max("number"))["m"]
            seq = int(last.split("-")[-1]) + 1 if last else 1
            self.number = f"RFQ-{year}-{seq:04d}"
        if not self.sla_due_at and self.priority:
            hours = settings.RFQ_SLA_HOURS.get(self.priority, 24)
            self.sla_due_at = (self.created_at or timezone.now()) + timezone.timedelta(hours=hours)
        return super().save(*args, **kwargs)

    # ------------------------------------------------------------ محاسبات
    @property
    def subtotal(self) -> int:
        return sum(line.line_total for line in self.lines.all())

    @property
    def discount_amount(self) -> int:
        return int(round(self.subtotal * float(self.discount_pct or 0) / 100))

    @property
    def vat(self) -> int:
        if self.company and self.company.vat_exempt:
            return 0
        return int(round((self.subtotal - self.discount_amount) * settings.VAT_RATE / 100))

    @property
    def total(self) -> int:
        return self.subtotal - self.discount_amount + self.vat

    @property
    def is_open(self) -> bool:
        return self.status in ("new", "tech_review", "pricing", "sent", "negotiation")

    @property
    def is_sla_overdue(self) -> bool:
        return bool(self.is_open and self.sla_due_at and timezone.now() > self.sla_due_at)

    @property
    def sla_remaining_hours(self) -> float | None:
        if not self.sla_due_at:
            return None
        delta = self.sla_due_at - timezone.now()
        return round(delta.total_seconds() / 3600, 1)

    @property
    def status_color(self) -> str:
        return {
            "new": "#64748b", "tech_review": "#1d4ed8", "pricing": "#6d28d9",
            "sent": "#12855f", "negotiation": "#b45309", "won": "#12855f",
            "converted": "#0e7490", "lost": "#c02626", "expired": "#c02626",
        }.get(self.status, "#64748b")

    @property
    def days_to_expiry(self) -> int | None:
        if not self.valid_until:
            return None
        return (self.valid_until - timezone.localdate()).days

    @property
    def items_summary(self) -> str:
        lines = list(self.lines.all()[:3])
        text = "، ".join(f"{line.product.name}" for line in lines)
        extra = self.lines.count() - len(lines)
        return text + (f" و {extra} قلم دیگر" if extra > 0 else "")


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, verbose_name="استعلام", on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.PROTECT,
                                related_name="quote_lines")
    qty = models.DecimalField("تعداد", max_digits=12, decimal_places=2, default=1)
    list_price = models.BigIntegerField("قیمت لیست (تومان)", default=0)
    offered_price = models.BigIntegerField("قیمت پیشنهادی واحد (تومان)", default=0)
    discount_pct = models.DecimalField("درصد تخفیف ردیف", max_digits=5, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField("زمان تأمین (روز)", default=0)
    availability_note = models.CharField("یادداشت موجودی", max_length=160, blank=True,
                                         help_text="مثلاً: تحویل ۴۵ روزه، ساخت به سفارش")
    note = models.CharField("توضیح ردیف", max_length=200, blank=True)

    class Meta:
        verbose_name = "ردیف استعلام"
        verbose_name_plural = "ردیف‌های استعلام"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.product.code} × {self.qty}"

    @property
    def line_total(self) -> int:
        return int(Decimal(self.qty) * Decimal(self.offered_price or self.list_price or 0))

    def apply_price(self, company=None, save: bool = True):
        """قیمت را از موتور قیمت‌گذاری پر می‌کند."""
        from pricing.services import resolve_price

        result = resolve_price(self.product, company=company, qty=float(self.qty))
        self.list_price = result.list_price
        self.offered_price = result.unit_price
        self.discount_pct = Decimal(str(result.total_discount_pct))
        if not self.lead_time_days:
            self.lead_time_days = self.product.lead_time_days
        if save:
            self.save(update_fields=["list_price", "offered_price", "discount_pct", "lead_time_days"])
        return result


class QuoteMessage(models.Model):
    """پیام‌های مذاکره — با تفکیک یادداشت داخلی از پیام قابل‌نمایش به مشتری."""

    quote = models.ForeignKey(Quote, verbose_name="استعلام", on_delete=models.CASCADE,
                              related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="نویسنده", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="quote_messages")
    author_name = models.CharField("نام نمایشی", max_length=100, blank=True)
    is_internal = models.BooleanField("یادداشت داخلی", default=False,
                                      help_text="در صورت فعال بودن، مشتری این پیام را نمی‌بیند.")
    kind = models.CharField("نوع پیام", max_length=15, default="message",
                            choices=[("message", "پیام"), ("offer", "ارسال پیشنهاد"),
                                     ("revision", "بازنگری قیمت"), ("status", "تغییر وضعیت"),
                                     ("note", "یادداشت")])
    body = models.TextField("متن")
    created_at = models.DateTimeField("زمان", default=timezone.now)

    class Meta:
        verbose_name = "پیام مذاکره"
        verbose_name_plural = "پیام‌های مذاکره"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.quote.number} — {self.body[:40]}"

    @property
    def display_author(self) -> str:
        if self.author_id:
            return self.author.get_full_name() or self.author.username
        return self.author_name or "مشتری"
