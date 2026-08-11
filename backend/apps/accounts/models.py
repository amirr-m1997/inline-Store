from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re


def normalize_iranian_phone(value):
    value = re.sub(r"[\s\-()]", "", value or "")
    if value.startswith("0098"): value = "+98" + value[4:]
    elif value.startswith("98") and not value.startswith("+98"): value = "+" + value
    elif value.startswith("0"): value = "+98" + value[1:]
    if not re.fullmatch(r"\+989\d{9}", value):
        raise ValidationError("شماره موبایل ایران معتبر نیست.")
    return value

class User(AbstractUser):
    class CustomerType(models.TextChoices):
        PERSONAL = "personal", "شخصی"
        BUSINESS = "business", "حقوقی"
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=16, unique=True, blank=True, null=True)
    landline = models.CharField(max_length=32, blank=True)
    customer_type = models.CharField(max_length=16, choices=CustomerType.choices, default=CustomerType.PERSONAL)
    company_name = models.CharField(max_length=255, blank=True)
    national_id = models.CharField(max_length=32, blank=True)
    economic_code = models.CharField(max_length=32, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower() if self.email else None
        self.phone = normalize_iranian_phone(self.phone) if self.phone else None
        super().save(*args, **kwargs)


class CustomerAddress(models.Model):
    user = models.ForeignKey(User, related_name="delivery_addresses", on_delete=models.CASCADE)
    title = models.CharField("عنوان نشانی", max_length=100)
    recipient_name = models.CharField("نام تحویل‌گیرنده", max_length=255)
    recipient_phone = models.CharField("شماره تحویل‌گیرنده", max_length=16)
    province = models.CharField("استان", max_length=100)
    city = models.CharField("شهر", max_length=100)
    postal_code = models.CharField("کدپستی", max_length=20, blank=True)
    address = models.TextField("نشانی")
    is_default = models.BooleanField("نشانی پیش‌فرض", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_default", "id")
        verbose_name = "نشانی مشتری"
        verbose_name_plural = "نشانی‌های مشتری"

    def __str__(self): return f"{self.user} — {self.title}"


class PhoneOTP(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "ورود"
        PASSWORD_RESET = "password_reset", "بازیابی رمز"
    phone = models.CharField(max_length=16, db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    consumed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "کد یکبار مصرف"
        verbose_name_plural = "کدهای یکبار مصرف"


class GoogleIdentity(models.Model):
    user = models.OneToOneField(User, related_name="google_identity", on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "هویت گوگل"
        verbose_name_plural = "هویت‌های گوگل"
