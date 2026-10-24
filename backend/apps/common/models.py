"""مدل‌های زیرساختی مشترک پنل مدیریت فروشگاه."""
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """ردیابی تغییرات مدل‌های عملیاتی فروشگاه در همان دیتابیس اصلی."""

    class Action(models.TextChoices):
        CREATE = "create", "ایجاد"
        UPDATE = "update", "ویرایش"
        DELETE = "delete", "حذف"

    created_at = models.DateTimeField("زمان رخداد", auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="کاربر",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField("عملیات", max_length=10, choices=Action.choices, db_index=True)
    app_label = models.CharField("بخش", max_length=64, db_index=True)
    model_name = models.CharField("مدل", max_length=64, db_index=True)
    object_id = models.CharField("شناسه رکورد", max_length=64, db_index=True)
    object_repr = models.CharField("رکورد", max_length=255)
    changes = models.JSONField("تغییرات", default=dict, blank=True)
    request_method = models.CharField("روش درخواست", max_length=10, blank=True)
    request_path = models.CharField("مسیر درخواست", max_length=500, blank=True)
    remote_addr = models.GenericIPAddressField("IP", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("app_label", "model_name", "object_id")),
            models.Index(fields=("actor", "-created_at")),
        ]
        verbose_name = "رخداد حسابرسی"
        verbose_name_plural = "رخدادهای حسابرسی"

    def __str__(self):
        return f"{self.get_action_display()} — {self.object_repr}"
