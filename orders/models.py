"""سفارش، ردیف‌ها، قواعد و مراحل گردش تأیید."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

ORDER_STATUS = [
    ("draft", "پیش‌نویس"),
    ("pending_approval", "در انتظار تأیید"),
    ("approved", "تأییدشده"),
    ("reserved", "رزرو موجودی"),
    ("ready", "آماده ارسال"),
    ("shipped", "ارسال‌شده"),
    ("delivered", "تحویل‌شده"),
    ("closed", "بسته‌شده"),
    ("cancelled", "لغو‌شده"),
]

PAYMENT_METHODS = [
    ("cash", "نقدی"),
    ("card", "کارت‌به‌کارت"),
    ("transfer", "حواله بانکی"),
    ("cheque", "چک"),
    ("credit", "اعتباری"),
    ("mixed", "ترکیبی"),
    ("gateway", "درگاه پرداخت"),
]

SHIPPING_METHODS = [
    ("pickup", "تحویل درب کارخانه"),
    ("freight", "باربری"),
    ("courier", "پیک"),
    ("customer", "حمل توسط مشتری"),
    ("install", "حمل و نصب توسط مهراصل"),
]


class Order(models.Model):
    """سفارش فروش با PO مشتری، گردش تأیید و اطلاعات حمل."""

    number = models.CharField("شماره سفارش", max_length=25, unique=True, blank=True)
    company = models.ForeignKey("customers.Company", verbose_name="مشتری", on_delete=models.PROTECT,
                                related_name="orders")
    contact = models.ForeignKey("customers.CompanyUser", verbose_name="کاربر خرید", null=True,
                                blank=True, on_delete=models.SET_NULL, related_name="orders")
    po_number = models.CharField("شماره سفارش خرید مشتری (PO)", max_length=40, blank=True)
    project_name = models.CharField("پروژه", max_length=160, blank=True)

    status = models.CharField("وضعیت", max_length=18, choices=ORDER_STATUS, default="draft", db_index=True)
    payment_method = models.CharField("روش پرداخت", max_length=10, choices=PAYMENT_METHODS, default="cash")
    payment_terms = models.CharField("شرایط تسویه", max_length=120, blank=True)
    discount_pct = models.DecimalField("درصد تخفیف کل", max_digits=5, decimal_places=2, default=0)
    shipping_cost = models.BigIntegerField("هزینه حمل (تومان)", default=0)
    shipping_method = models.CharField("روش حمل", max_length=10, choices=SHIPPING_METHODS, default="pickup")
    shipping_address = models.ForeignKey("customers.CompanyAddress", verbose_name="آدرس تحویل",
                                         null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name="orders")
    waybill_number = models.CharField("شماره بارنامه", max_length=40, blank=True)
    carrier_name = models.CharField("باربری/راننده", max_length=100, blank=True)

    sales_rep = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="کارشناس فروش", null=True,
                                  blank=True, on_delete=models.SET_NULL, related_name="orders")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True,
                                   blank=True, on_delete=models.SET_NULL, related_name="orders_created")
    placed_by_rep_for_company = models.BooleanField("ثبت‌شده به‌نیابت از مشتری", default=False)

    ordered_at = models.DateTimeField("تاریخ ثبت", default=timezone.now, db_index=True)
    approved_at = models.DateTimeField("تاریخ تأیید", null=True, blank=True)
    expected_delivery_at = models.DateField("تاریخ تحویل تعهدی", null=True, blank=True)
    shipped_at = models.DateTimeField("تاریخ ارسال", null=True, blank=True)
    delivered_at = models.DateTimeField("تاریخ تحویل", null=True, blank=True)

    customer_note = models.TextField("یادداشت مشتری", blank=True)
    internal_note = models.TextField("یادداشت داخلی", blank=True)
    cancel_reason = models.CharField("دلیل لغو", max_length=200, blank=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["status", "ordered_at"]),
                   models.Index(fields=["company", "status"])]

    def __str__(self) -> str:
        return f"{self.number} — {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.number:
            from django.db.models import Max

            year = (timezone.now().astimezone().year - 621)
            prefix = f"SO-{year}-"
            last = Order.objects.filter(number__startswith=prefix).aggregate(m=Max("number"))["m"]
            seq = int(last.split("-")[-1]) + 1 if last else 1000
            self.number = f"{prefix}{seq}"
        return super().save(*args, **kwargs)

    # ---------------------------------------------------------- محاسبات
    @property
    def subtotal(self) -> int:
        return sum(line.line_total for line in self.lines.all())

    @property
    def discount_amount(self) -> int:
        return int(round(self.subtotal * float(self.discount_pct or 0) / 100))

    @property
    def net_amount(self) -> int:
        return self.subtotal - self.discount_amount

    @property
    def vat(self) -> int:
        if self.company and self.company.vat_exempt:
            return 0
        return int(round((self.net_amount + self.shipping_cost) * settings.VAT_RATE / 100))

    @property
    def total(self) -> int:
        return self.net_amount + self.shipping_cost + self.vat

    @property
    def paid_amount(self) -> int:
        return sum(payment.amount for payment in self.payments.all())

    @property
    def balance(self) -> int:
        return max(self.total - self.paid_amount, 0)

    @property
    def source_quote(self):
        """استعلام مبدأ این سفارش (اگر از استعلام ساخته شده باشد)."""
        return self.source_quotes.first()

    @property
    def status_color(self) -> str:
        return {
            "draft": "#64748b", "pending_approval": "#b45309", "approved": "#12855f",
            "reserved": "#0e7490", "ready": "#0891b2", "shipped": "#1d4ed8",
            "delivered": "#12855f", "closed": "#475569", "cancelled": "#c02626",
        }.get(self.status, "#64748b")

    @property
    def credit_info(self) -> dict:
        """وضعیت اعتبار مشتری برای این سفارش."""
        company = self.company
        return {
            "limit": company.credit_limit,
            "used": company.credit_used,
            "available": company.credit_available,
            "exceeded": bool(company.credit_limit and self.total > company.credit_available),
            "usage_pct": company.credit_usage_pct,
        }

    @property
    def pending_approvals(self):
        return self.approvals.filter(status="pending")

    @property
    def is_fully_shipped(self) -> bool:
        return all(float(line.qty_shipped) >= float(line.qty) for line in self.lines.all())

    @property
    def profit_margin_pct(self) -> float | None:
        """حاشیه سود ناخالص تقریبی بر اساس بهای انبار."""
        cost = sum(float(line.qty) * float(line.unit_cost) for line in self.lines.all())
        if not cost:
            return None
        return round((self.net_amount - cost) * 100 / self.net_amount, 1) if self.net_amount else None


class OrderLine(models.Model):
    order = models.ForeignKey(Order, verbose_name="سفارش", on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", verbose_name="محصول", on_delete=models.PROTECT,
                                related_name="order_lines")
    warehouse = models.ForeignKey("inventory.Warehouse", verbose_name="انبار", null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="order_lines")
    qty = models.DecimalField("تعداد", max_digits=12, decimal_places=2, default=1)
    unit_price = models.BigIntegerField("قیمت واحد (تومان)", default=0)
    list_price = models.BigIntegerField("قیمت لیست (تومان)", default=0)
    unit_cost = models.BigIntegerField("بهای تمام‌شده (تومان)", default=0)
    discount_pct = models.DecimalField("درصد تخفیف", max_digits=5, decimal_places=2, default=0)
    qty_reserved = models.DecimalField("رزرو‌شده", max_digits=12, decimal_places=2, default=0)
    qty_shipped = models.DecimalField("ارسال‌شده", max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField("زمان تأمین (روز)", default=0)
    spec_note = models.CharField("مشخصات سفارش", max_length=200, blank=True)

    class Meta:
        verbose_name = "ردیف سفارش"
        verbose_name_plural = "ردیف‌های سفارش"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.product.code} × {self.qty}"

    @property
    def line_total(self) -> int:
        return int(Decimal(self.qty) * Decimal(self.unit_price or 0))

    @property
    def remaining_to_ship(self) -> Decimal:
        return max(Decimal(self.qty) - Decimal(self.qty_shipped), Decimal("0"))


class ApprovalRule(models.Model):
    """قاعده‌ی گردش تأیید: چه چیزی، تا چه مبلغی، توسط چه نقشی تأیید شود."""

    SCOPES = [
        ("order_amount", "مبلغ سفارش"),
        ("discount_pct", "درصد تخفیف"),
        ("credit_exceed", "عبور از سقف اعتبار"),
        ("payment_terms", "شرایط تسویه خاص"),
    ]

    name = models.CharField("عنوان قاعده", max_length=140)
    scope = models.CharField("دامنه", max_length=20, choices=SCOPES)
    threshold = models.BigIntegerField("آستانه", default=0,
                                       help_text="مبلغ به تومان یا درصد، بسته به دامنه")
    approver_role = models.CharField("نقش تأییدکننده", max_length=20, default="sales_manager",
                                     choices=[("sales_manager", "مدیر فروش"),
                                              ("finance", "مدیر مالی"),
                                              ("sysadmin", "مدیر سیستم")])
    step = models.PositiveIntegerField("ترتیب مرحله", default=1)
    is_active = models.BooleanField("فعال", default=True)
    note = models.CharField("یادداشت", max_length=200, blank=True)

    class Meta:
        verbose_name = "قاعده تأیید"
        verbose_name_plural = "قواعد گردش تأیید"
        ordering = ["scope", "step", "threshold"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_scope_display()} ≥ {self.threshold})"

    def matches(self, order) -> bool:
        if self.scope == "order_amount":
            return order.net_amount >= self.threshold
        if self.scope == "discount_pct":
            return float(order.discount_pct or 0) >= self.threshold
        if self.scope == "credit_exceed":
            info = order.credit_info
            return bool(info["exceeded"])
        if self.scope == "payment_terms":
            return order.payment_method in ("cheque", "credit", "mixed")
        return False


class Approval(models.Model):
    """مرحله‌ی تأیید یک سفارش (زنجیره‌ی قابل پیگیری)."""

    STATUS = [("pending", "در انتظار"), ("approved", "تأییدشده"), ("rejected", "ردشده"),
              ("skipped", "عبور‌کرده")]

    order = models.ForeignKey(Order, verbose_name="سفارش", on_delete=models.CASCADE,
                              related_name="approvals")
    rule = models.ForeignKey(ApprovalRule, verbose_name="قاعده", null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="approvals")
    step = models.PositiveIntegerField("مرحله", default=1)
    required_role = models.CharField("نقش لازم", max_length=20, default="sales_manager")
    status = models.CharField("وضعیت", max_length=10, choices=STATUS, default="pending", db_index=True)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="تأییدکننده", null=True,
                                 blank=True, on_delete=models.SET_NULL, related_name="approvals")
    comment = models.CharField("توضیح", max_length=255, blank=True)
    amount_snapshot = models.BigIntegerField("مبلغ در زمان تأیید", default=0)
    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    acted_at = models.DateTimeField("زمان اقدام", null=True, blank=True)

    class Meta:
        verbose_name = "مرحله تأیید"
        verbose_name_plural = "گردش تأیید سفارش‌ها"
        ordering = ["order", "step"]

    def __str__(self) -> str:
        return f"{self.order.number} — مرحله {self.step} ({self.get_status_display()})"

    @property
    def source_quote(self):
        """استعلام مبدأ این سفارش (اگر از استعلام ساخته شده باشد)."""
        return self.source_quotes.first()

    @property
    def status_color(self) -> str:
        return {"pending": "#b45309", "approved": "#12855f", "rejected": "#c02626",
                "skipped": "#64748b"}.get(self.status, "#64748b")


class OrderEvent(models.Model):
    """تایم‌لاین سفارش برای نمایش در پنل."""

    order = models.ForeignKey(Order, verbose_name="سفارش", on_delete=models.CASCADE,
                              related_name="events")
    KIND_CHOICES = [
        ("status", "تغییر وضعیت"),
        ("approval", "گردش تأیید"),
        ("reject", "رد سفارش"),
        ("stock", "رزرو / کسری موجودی"),
        ("ship", "ارسال"),
        ("delivery", "تحویل"),
        ("invoice", "صدور فاکتور"),
        ("commitment", "تعهد و قرارداد"),
        ("note", "یادداشت"),
        ("cancel", "لغو"),
    ]
    kind = models.CharField("نوع", max_length=20, choices=KIND_CHOICES, default="note")
    title = models.CharField("عنوان", max_length=200)
    description = models.CharField("توضیح", max_length=255, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="کاربر", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="order_events")
    created_at = models.DateTimeField("زمان", default=timezone.now)

    class Meta:
        verbose_name = "رخداد سفارش"
        verbose_name_plural = "خط زمانی سفارش"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
