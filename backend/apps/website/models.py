from django.db import models


class SiteNavigation(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=100)
    title_en = models.CharField("عنوان انگلیسی", max_length=100, blank=True)
    url = models.CharField("نشانی", max_length=255)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    icon = models.CharField("آیکن", max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "ناوبری وب‌سایت"
        verbose_name_plural = "ناوبری وب‌سایت"

    def __str__(self):
        return self.title_fa


class FooterSection(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=100)
    title_en = models.CharField("عنوان انگلیسی", max_length=100, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "بخش فوتر"
        verbose_name_plural = "بخش‌های فوتر"

    def __str__(self):
        return self.title_fa


class FooterLink(models.Model):
    section = models.ForeignKey(FooterSection, related_name="links", on_delete=models.CASCADE, verbose_name="بخش")
    title_fa = models.CharField("عنوان فارسی", max_length=100)
    title_en = models.CharField("عنوان انگلیسی", max_length=100, blank=True)
    url = models.CharField("نشانی", max_length=500)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    open_in_new_tab = models.BooleanField("باز شدن در صفحه جدید", default=False)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "پیوند فوتر"
        verbose_name_plural = "پیوندهای فوتر"

    def __str__(self):
        return self.title_fa


class TrustBadge(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=100)
    title_en = models.CharField("عنوان انگلیسی", max_length=100, blank=True)
    image = models.ImageField("تصویر نشان", upload_to="footer/trust-badges/", blank=True, null=True)
    url = models.URLField("نشانی مقصد", blank=True)
    alt_fa = models.CharField("متن جایگزین فارسی", max_length=255, blank=True)
    alt_en = models.CharField("متن جایگزین انگلیسی", max_length=255, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "نشان اعتماد"
        verbose_name_plural = "نشان‌های اعتماد"

    def __str__(self):
        return self.title_fa


class ContactMessage(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "جدید"
        IN_PROGRESS = "in_progress", "در حال بررسی"
        RESOLVED = "resolved", "پاسخ داده شده"

    full_name = models.CharField("نام و نام خانوادگی", max_length=255)
    phone = models.CharField("شماره تماس", max_length=64)
    email = models.EmailField("ایمیل", blank=True)
    subject = models.CharField("موضوع", max_length=255)
    message = models.TextField("پیام", max_length=5000)
    status = models.CharField("وضعیت", max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("زمان ارسال", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self):
        return f"{self.full_name} — {self.subject}"
