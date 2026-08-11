from django.db import models


class CompanyInfo(models.Model):
    name_fa = models.CharField("نام فارسی شرکت", max_length=255)
    logo = models.ImageField("لوگو", upload_to="company/", blank=True, null=True)
    description = models.TextField("توضیحات", blank=True)
    address = models.TextField("نشانی", blank=True)
    phone = models.CharField("تلفن", max_length=64, blank=True)
    mobile = models.CharField("موبایل", max_length=64, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    website = models.URLField("وب‌سایت", blank=True)
    working_hours = models.CharField("ساعات کاری", max_length=255, blank=True)
    footer_copyright_fa = models.CharField("متن کپی‌رایت فارسی", max_length=500, blank=True)
    footer_copyright_en = models.CharField("متن کپی‌رایت انگلیسی", max_length=500, blank=True)
    hero_title_fa = models.CharField("عنوان هیرو فارسی", max_length=255, blank=True)
    hero_title_en = models.CharField("عنوان هیرو انگلیسی", max_length=255, blank=True)
    hero_slogan_fa = models.CharField("شعار هیرو فارسی", max_length=255, blank=True)
    hero_slogan_en = models.CharField("شعار هیرو انگلیسی", max_length=255, blank=True)
    hero_description_fa = models.TextField("توضیحات هیرو فارسی", blank=True)
    hero_description_en = models.TextField("توضیحات هیرو انگلیسی", blank=True)
    hero_image = models.ImageField("تصویر هیرو", upload_to="company/hero/", blank=True, null=True)
    mobile_hero_image = models.ImageField("تصویر موبایل هیرو", upload_to="company/hero/", blank=True, null=True)
    primary_button_text = models.CharField("متن دکمه اصلی", max_length=100, blank=True)
    primary_button_link = models.CharField("لینک دکمه اصلی", max_length=255, blank=True)
    secondary_button_text = models.CharField("متن دکمه دوم", max_length=100, blank=True)
    secondary_button_link = models.CharField("لینک دکمه دوم", max_length=255, blank=True)
    hero_is_active = models.BooleanField("فعال بودن هیرو", default=True)
    hero_created_at = models.DateTimeField("ایجاد هیرو", auto_now_add=True)
    hero_updated_at = models.DateTimeField("به‌روزرسانی هیرو", auto_now=True)

    class Meta:
        verbose_name = "اطلاعات شرکت"
        verbose_name_plural = "اطلاعات شرکت"

    def __str__(self):
        return self.name_fa


class CompanyAdvantage(models.Model):
    title_fa = models.CharField("عنوان فارسی", max_length=255)
    title_en = models.CharField("عنوان انگلیسی", max_length=255, blank=True)
    description_fa = models.CharField("توضیح فارسی", max_length=255, blank=True)
    description_en = models.CharField("توضیح انگلیسی", max_length=255, blank=True)
    icon = models.CharField("آیکن", max_length=64, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "مزیت شرکت"
        verbose_name_plural = "مزیت‌های شرکت"

    def __str__(self):
        return self.title_fa
