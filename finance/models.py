"""مالی: فاکتور (و وضعیت سامانه مؤدیان)، پرداخت و چک."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.palette import ACCENT, DANGER, INFO, MUTED, OK, SLATE, WARN

INVOICE_STATUS = [
    ("draft", "پیش‌نویس"),
    ("issued", "صادرشده"),
    ("sent", "ارسال به سامانه مؤدیان"),
    ("accepted", "پذیرفته‌شده در مؤدیان"),
    ("rejected", "ردشده در مؤدیان"),
    ("partially_paid", "پرداخت جزئی"),
    ("paid", "تسویه‌شده"),
    ("overdue", "معوق"),
    ("cancelled", "لغو‌شده"),
]

MOADIAN_STATUS = [
    ("not_sent", "ارسال‌نشده"),
    ("pending", "در صف ارسال"),
    ("submitted", "ارسال‌شده"),
    ("accepted", "تأیید سامانه"),
    ("failed", "خطای اعتبارسنجی"),
]

INVOICE_KINDS = [
    ("proforma", "پیش‌فاکتور"),
    ("official", "فاکتور رسمی"),
    ("unofficial", "فاکتور غیررسمی"),
    ("return", "برگشت از فروش"),
]

PAYMENT_METHODS = [
    ("cash", "نقدی"),
    ("card", "کارت‌به‌کارت"),
    ("transfer", "حواله بانکی"),
    ("cheque", "چک"),
    ("gateway", "درگاه پرداخت"),
    ("credit", "تسویه اعتباری"),
]

CHEQUE_STATUS = [
    ("in_hand", "در جریان (نزد ما)"),
    ("deposited", "سپرده‌شده به بانک"),
    ("cleared", "وصول‌شده"),
    ("bounced", "برگشتی"),
    ("returned", "برگشت به مشتری"),
]


class Invoice(models.Model):
    """فاکتور فروش / پیش‌فاکتور با وضعیت سامانه مؤدیان."""

    number = models.CharField("شماره فاکتور", max_length=25, unique=True, blank=True)
    kind = models.CharField("نوع سند", max_length=10, choices=INVOICE_KINDS, default="official")
    order = models.ForeignKey("orders.Order", verbose_name="سفارش", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="invoices")
    company = models.ForeignKey("customers.Company", verbose_name="مشتری", on_delete=models.PROTECT,
                                related_name="invoices")

    status = models.CharField("وضعیت", max_length=15, choices=INVOICE_STATUS, default="draft", db_index=True)
    subtotal = models.BigIntegerField("جمع اقلام (تومان)", default=0)
    discount_amount = models.BigIntegerField("تخفیف (تومان)", default=0)
    vat_amount = models.BigIntegerField("ارزش افزوده (تومان)", default=0)
    shipping_amount = models.BigIntegerField("هزینه حمل (تومان)", default=0)
    total = models.BigIntegerField("مبلغ کل (تومان)", default=0)
    paid_amount = models.BigIntegerField("مبلغ پرداخت‌شده (تومان)", default=0)

    issued_at = models.DateField("تاریخ صدور", default=timezone.localdate)
    due_date = models.DateField("سررسید", null=True, blank=True)
    settled_at = models.DateField("تاریخ تسویه", null=True, blank=True)

    # سامانه مؤدیان (الزام قانونی)
    moadian_status = models.CharField("وضعیت مؤدیان", max_length=12, choices=MOADIAN_STATUS,
                                      default="not_sent", db_index=True)
    moadian_tax_id = models.CharField("شماره مالیاتی یکتا", max_length=40, blank=True)
    moadian_sent_at = models.DateTimeField("زمان ارسال به مؤدیان", null=True, blank=True)
    moadian_error = models.CharField("خطای مؤدیان", max_length=255, blank=True)
    buyer_economic_code = models.CharField("کد اقتصادی خریدار", max_length=15, blank=True)

    note = models.CharField("توضیح", max_length=255, blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True,
                                   blank=True, on_delete=models.SET_NULL, related_name="invoices_created")

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها و پیش‌فاکتورها"
        ordering = ["-issued_at", "-id"]
        indexes = [models.Index(fields=["status", "issued_at"]),
                   models.Index(fields=["moadian_status"])]

    def __str__(self) -> str:
        return f"{self.number} — {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.number:
            from django.db.models import Max

            prefix = {"official": "INV", "proforma": "PF", "unofficial": "NINV", "return": "RET"}.get(
                self.kind, "INV")
            year = (timezone.now().astimezone().year - 621)
            start = f"{prefix}-{year}-"
            last = Invoice.objects.filter(number__startswith=start).aggregate(m=Max("number"))["m"]
            seq = int(last.split("-")[-1]) + 1 if last else 1
            self.number = f"{start}{seq:05d}"
        return super().save(*args, **kwargs)

    @property
    def balance(self) -> int:
        return max(self.total - self.paid_amount, 0)

    @property
    def status_color(self) -> str:
        return {
            "draft": MUTED, "issued": INFO, "sent": ACCENT,
            "accepted": OK, "rejected": DANGER, "partially_paid": WARN,
            "paid": OK, "overdue": DANGER, "cancelled": SLATE,
        }.get(self.status, MUTED)

    @property
    def moadian_color(self) -> str:
        return {
            "not_sent": MUTED, "pending": WARN, "submitted": ACCENT,
            "accepted": OK, "failed": DANGER,
        }.get(self.moadian_status, MUTED)

    @property
    def days_overdue(self) -> int | None:
        if not self.due_date or self.status in ("paid", "cancelled"):
            return None
        delta = (timezone.localdate() - self.due_date).days
        return delta if delta > 0 else 0

    def recalculate(self, save: bool = True):
        """محاسبه‌ی مجدد مبالغ از روی ردیف‌ها."""
        subtotal = sum(line.line_total for line in self.lines.all())
        self.subtotal = subtotal
        base = subtotal - self.discount_amount + self.shipping_amount
        if not self.company.vat_exempt:
            self.vat_amount = int(round(base * settings.VAT_RATE / 100)) if not self.vat_amount else self.vat_amount
        self.total = base + self.vat_amount
        if save:
            self.save(update_fields=["subtotal", "total", "vat_amount"])
        return self.total


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, verbose_name="فاکتور", on_delete=models.CASCADE,
                                related_name="lines")
    product = models.ForeignKey("catalog.Product", verbose_name="محصول", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="invoice_lines")
    title = models.CharField("شرح کالا/خدمت", max_length=220)
    qty = models.DecimalField("تعداد", max_digits=12, decimal_places=2, default=1)
    unit_price = models.BigIntegerField("قیمت واحد (تومان)", default=0)
    discount_pct = models.DecimalField("درصد تخفیف", max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = "ردیف فاکتور"
        verbose_name_plural = "ردیف‌های فاکتور"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.title} × {self.qty}"

    @property
    def line_total(self) -> int:
        gross = Decimal(self.qty) * Decimal(self.unit_price or 0)
        return int(round(gross * (1 - Decimal(str(self.discount_pct or 0)) / 100)))


class Payment(models.Model):
    """پرداخت دریافتی (نقد/کارت/حواله/چک)."""

    invoice = models.ForeignKey(Invoice, verbose_name="فاکتور", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="payments")
    order = models.ForeignKey("orders.Order", verbose_name="سفارش", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="payments")
    company = models.ForeignKey("customers.Company", verbose_name="مشتری", on_delete=models.PROTECT,
                                related_name="payments")
    method = models.CharField("روش پرداخت", max_length=10, choices=PAYMENT_METHODS, default="transfer")
    amount = models.BigIntegerField("مبلغ (تومان)")
    paid_at = models.DateField("تاریخ پرداخت", default=timezone.localdate)
    reference = models.CharField("شماره پیگیری/حواله", max_length=60, blank=True)
    bank = models.CharField("بانک", max_length=50, blank=True)
    note = models.CharField("توضیح", max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True,
                                   blank=True, on_delete=models.SET_NULL, related_name="payments_created")
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-paid_at", "-id"]

    def __str__(self) -> str:
        return f"{self.get_method_display()} {self.amount:,} — {self.company.name}"

    def apply_to_invoice(self, save: bool = True):
        """به‌روزرسانی مبلغ پرداخت‌شده و وضعیت فاکتور مرجع."""
        if not self.invoice_id:
            return
        invoice = self.invoice
        invoice.paid_amount = sum(p.amount for p in invoice.payments.all())
        if invoice.paid_amount >= invoice.total:
            invoice.status = "paid"
            invoice.settled_at = self.paid_at
        elif invoice.paid_amount > 0:
            invoice.status = "partially_paid"
        if save:
            invoice.save(update_fields=["paid_amount", "status", "settled_at"])


class Cheque(models.Model):
    """چک دریافتی/پرداختی با سررسید و چرخه‌ی وصول (الگوی رایج فروش B2B ایران)."""

    DIRECTION = [("received", "دریافتی از مشتری"), ("issued", "پرداختی به تأمین‌کننده")]

    company = models.ForeignKey("customers.Company", verbose_name="طرف حساب", on_delete=models.PROTECT,
                                related_name="cheques")
    direction = models.CharField("جهت", max_length=8, choices=DIRECTION, default="received")
    number = models.CharField("شماره چک", max_length=30)
    bank = models.CharField("بانک", max_length=50)
    branch = models.CharField("شعبه", max_length=60, blank=True)
    account_holder = models.CharField("صاحب حساب", max_length=120, blank=True)
    amount = models.BigIntegerField("مبلغ (تومان)")
    issue_date = models.DateField("تاریخ صدور", null=True, blank=True)
    due_date = models.DateField("تاریخ سررسید", db_index=True)
    status = models.CharField("وضعیت", max_length=10, choices=CHEQUE_STATUS, default="in_hand", db_index=True)

    invoice = models.ForeignKey(Invoice, verbose_name="فاکتور مرتبط", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="cheques")
    order = models.ForeignKey("orders.Order", verbose_name="سفارش مرتبط", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="cheques")
    deposited_at = models.DateField("تاریخ سپرده به بانک", null=True, blank=True)
    cleared_at = models.DateField("تاریخ وصول", null=True, blank=True)
    bounce_reason = models.CharField("علت برگشت", max_length=200, blank=True)
    note = models.CharField("توضیح", max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True,
                                   blank=True, on_delete=models.SET_NULL, related_name="cheques_created")
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "چک"
        verbose_name_plural = "چک‌ها و سررسیدها"
        ordering = ["due_date"]
        unique_together = ("company", "direction", "number", "bank")
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self) -> str:
        return f"چک {self.number} — {self.company.name}"

    @property
    def days_to_due(self) -> int:
        return (self.due_date - timezone.localdate()).days

    @property
    def status_color(self) -> str:
        return {
            "in_hand": ACCENT, "deposited": INFO, "cleared": OK,
            "bounced": DANGER, "returned": WARN,
        }.get(self.status, MUTED)

    @property
    def is_overdue(self) -> bool:
        return self.status in ("in_hand", "deposited") and self.days_to_due < 0

    @property
    def urgency(self) -> tuple[str, str]:
        """(برچسب، رنگ) برای هشدار سررسید."""
        if self.status in ("cleared", "returned"):
            return self.get_status_display(), OK
        days = self.days_to_due
        from core.utils import num as _num

        if days < 0:
            return f"{_num(abs(days), 0)} روز معوق", DANGER
        if days == 0:
            return "سررسید امروز", DANGER
        if days <= 7:
            return f"{_num(days, 0)} روز دیگر", WARN
        return f"{_num(days, 0)} روز دیگر", ACCENT
