"""کاربران پنل و نقش‌ها."""
from __future__ import annotations

from django.conf import settings
from django.db import models

ROLE_CHOICES = [
    ("sysadmin", "مدیر سیستم"),
    ("sales_manager", "مدیر فروش"),
    ("sales", "کارشناس فروش"),
    ("warehouse", "انباردار"),
    ("finance", "مالی"),
    ("content", "محتوا"),
    ("support", "پشتیبانی فنی"),
]


class Profile(models.Model):
    """پروفایل کاربر پنل: نقش سازمانی، تلفن و تنظیمات دسترسی."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="کاربر", on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField("نقش", max_length=30, choices=ROLE_CHOICES, default="sales")
    phone = models.CharField("تلفن همراه", max_length=20, blank=True)
    job_title = models.CharField("سمت", max_length=80, blank=True)
    branch = models.CharField("شعبه/دفتر", max_length=80, blank=True)
    can_approve_discount_upto = models.PositiveIntegerField(
        "سقف تخفیف مجاز (درصد)", default=0,
        help_text="کارشناس فروش تا این درصد می‌تواند تخفیف بدهد؛ بیشتر از آن نیاز به تأیید مدیر فروش دارد.",
    )
    can_approve_order_upto = models.BigIntegerField(
        "سقف تأیید سفارش (تومان)", default=0,
        help_text="سفارش بالاتر از این مبلغ نیاز به تأیید سطح بالاتر دارد.",
    )
    two_factor_enabled = models.BooleanField("ورود دوعاملی فعال", default=False)
    ip_allowlist = models.CharField(
        "IPهای مجاز (با کاما)", max_length=255, blank=True,
        help_text="خالی = بدون محدودیت. برای کاربران مالی و مدیر سیستم توصیه می‌شود.",
    )
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل کاربران پنل"

    def __str__(self) -> str:
        return f"{self.user.get_username()} — {self.get_role_display()}"

    # آسان‌سازی استفاده در قالب‌ها و کد
    @property
    def is_finance(self) -> bool:
        return self.role == "finance"

    @property
    def is_sales(self) -> bool:
        return self.role in ("sales", "sales_manager")

    @property
    def is_warehouse(self) -> bool:
        return self.role == "warehouse"

    @property
    def is_manager(self) -> bool:
        return self.role in ("sales_manager", "sysadmin")
