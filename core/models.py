"""مدل‌های هسته: لاگ حسابرسی و اعلان‌ها."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """لاگ حسابرسی — فقط درج می‌شود و قابل ویرایش/حذف نیست."""

    class Action(models.TextChoices):
        CREATE = "create", "ایجاد"
        UPDATE = "update", "ویرایش"
        DELETE = "delete", "حذف"
        STATUS = "status", "تغییر وضعیت"
        PRICE = "price", "تغییر قیمت"
        STOCK = "stock", "تغییر موجودی"
        LOGIN = "login", "ورود"
        LOGIN_FAILED = "login_failed", "ورود ناموفق"
        LOGOUT = "logout", "خروج"
        EXPORT = "export", "خروجی گرفتن"
        IMPORT = "import", "ورود داده"
        IMPERSONATE = "impersonate", "ورود به‌نیابت"
        APPROVE = "approve", "تأیید"
        REJECT = "reject", "رد"

    action = models.CharField("اقدام", max_length=20, choices=Action.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="کاربر",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    actor_repr = models.CharField("نام کاربر", max_length=120, blank=True)
    role = models.CharField("نقش در زمان رخداد", max_length=60, blank=True)

    model_name = models.CharField("مدل", max_length=120, blank=True, db_index=True)
    object_id = models.CharField("شناسه رکورد", max_length=40, blank=True)
    object_repr = models.CharField("عنوان رکورد", max_length=255, blank=True)

    before = models.JSONField("مقدار قبل", null=True, blank=True)
    after = models.JSONField("مقدار بعد", null=True, blank=True)
    changed_fields = models.JSONField("فیلدهای تغییر‌یافته", null=True, blank=True)

    reason = models.CharField("دلیل تغییر", max_length=255, blank=True)
    note = models.CharField("توضیح", max_length=255, blank=True)

    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.TextField("مرورگر", blank=True)
    created_at = models.DateTimeField("زمان", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "رخداد حسابرسی"
        verbose_name_plural = "سیاههٔ رخدادهای حسابرسی"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} — {self.model_name} #{self.object_id} ({self.actor_repr})"

    @property
    def diff_pairs(self):
        """جفت‌های «قبل ← بعد» برای نمایش در پنل."""
        if not isinstance(self.before, dict) or not isinstance(self.after, dict):
            return []
        pairs = []
        keys = set(self.before) | set(self.after)
        for key in sorted(keys):
            old, new = self.before.get(key), self.after.get(key)
            if old != new:
                pairs.append((key, old, new))
        return pairs

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("لاگ حسابرسی فقط درج‌شدنی است و قابل ویرایش نیست.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("لاگ حسابرسی قابل حذف نیست.")


class Notification(models.Model):
    """اعلان درون‌پنلی (هشدار موجودی، SLA استعلام، چک سررسید و ...)."""

    class Kind(models.TextChoices):
        LOW_STOCK = "low_stock", "موجودی کم"
        RFQ_SLA = "rfq_sla", "تأخیر استعلام"
        ORDER_PENDING = "order_pending", "سفارش معطل تأیید"
        PRICE_EXPIRING = "price_expiring", "قیمت در آستانه انقضا"
        CHEQUE_DUE = "cheque_due", "چک نزدیک سررسید"
        INVOICE_UNPAID = "invoice_unpaid", "فاکتور پرداخت‌نشده"
        CREDIT_EXCEED = "credit_exceed", "عبور از سقف اعتبار"
        DOC_PENDING = "doc_pending", "مدارک ناقص"
        REVIEW_PENDING = "review_pending", "در انتظار تأیید"

    class Level(models.TextChoices):
        INFO = "info", "اطلاع"
        SUCCESS = "success", "موفق"
        WARNING = "warning", "هشدار"
        DANGER = "danger", "بحرانی"

    kind = models.CharField("نوع", max_length=30, choices=Kind.choices, db_index=True)
    level = models.CharField("شدت", max_length=10, choices=Level.choices, default=Level.INFO)
    title = models.CharField("عنوان", max_length=200)
    body = models.TextField("متن", blank=True)
    url = models.CharField("لینک", max_length=300, blank=True)
    company = models.ForeignKey(
        "customers.Company", verbose_name="مشتری", null=True, blank=True,
        on_delete=models.CASCADE, related_name="notifications",
    )
    is_read = models.BooleanField("خوانده‌شده", default=False, db_index=True)
    dedup_key = models.CharField("کلید یکتا", max_length=120, unique=True, null=True, blank=True)
    created_at = models.DateTimeField("زمان", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_read", "level"])]

    def __str__(self) -> str:
        return self.title
