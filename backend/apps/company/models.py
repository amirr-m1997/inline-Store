from django.db import models


class SourcedContentModel(models.Model):
    source_url = models.URLField(blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    migration_notes = models.TextField(blank=True)

    class Meta:
        abstract = True


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


class CompanyLocation(SourcedContentModel):
    class LocationType(models.TextChoices):
        FACTORY = "factory", "کارخانه"
        OFFICE = "office", "دفتر"
        SHOWROOM = "showroom", "نمایشگاه"
        STORE = "store", "فروشگاه"
        REPRESENTATIVE = "representative", "نمایندگی"

    location_type = models.CharField(max_length=20, choices=LocationType.choices)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    address_fa = models.TextField(blank=True)
    address_en = models.TextField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    mobile = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)
    working_hours = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "مکان شرکت"
        verbose_name_plural = "مکان‌های شرکت"

    def __str__(self): return self.name_fa


class CompanyMilestone(SourcedContentModel):
    date_label = models.CharField(max_length=64, blank=True)
    title_fa = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255, blank=True)
    description_fa = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "نقطه عطف شرکت"
        verbose_name_plural = "نقاط عطف شرکت"

    def __str__(self): return self.title_fa


class CompanyCertification(SourcedContentModel):
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "تأیید نشده"
        PENDING = "pending", "در انتظار بررسی"
        VERIFIED = "verified", "تأیید شده"

    title_fa = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255, blank=True)
    issuer = models.CharField(max_length=255, blank=True)
    certificate_code = models.CharField(max_length=128, blank=True)
    file = models.FileField(upload_to="company/certifications/", blank=True, null=True)
    image = models.ImageField(upload_to="company/certifications/", blank=True, null=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=16, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    is_published = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "استاندارد / گواهی شرکت"
        verbose_name_plural = "استانداردها / گواهی‌های شرکت"

    def __str__(self): return self.title_fa


class CompanyHonor(SourcedContentModel):
    title_fa = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255, blank=True)
    issuer = models.CharField(max_length=255, blank=True)
    year_label = models.CharField(max_length=64, blank=True)
    description_fa = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    image = models.ImageField(upload_to="company/honors/", blank=True, null=True)
    file = models.FileField(upload_to="company/honors/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "افتخار شرکت"
        verbose_name_plural = "افتخارات شرکت"

    def __str__(self): return self.title_fa


class Industry(models.Model):
    slug = models.SlugField(unique=True)
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True)
    description_fa = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    image = models.ImageField(upload_to="company/industries/", blank=True, null=True)
    categories = models.ManyToManyField("catalog.Category", blank=True, related_name="industries")
    products = models.ManyToManyField("catalog.Product", blank=True, related_name="industries")
    capabilities = models.ManyToManyField("Capability", blank=True, related_name="industries")
    source_url = models.URLField(blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    migration_notes = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("order", "name_fa")
        verbose_name = "صنعت / کاربرد"
        verbose_name_plural = "صنایع / کاربردها"

    def __str__(self): return self.name_fa


class CompanySection(SourcedContentModel):
    class SectionType(models.TextChoices):
        INTRODUCTION = "introduction", "معرفی"
        VALUE = "value", "ارزش"
        HISTORY = "history", "سابقه"
        LOCATION = "location", "موقعیت"
        MEDIA = "media", "رسانه"
        CAPABILITIES = "capabilities", "توانمندی‌ها"

    section_type = models.CharField("نوع بخش", max_length=24, choices=SectionType.choices)
    title_fa = models.CharField("عنوان فارسی", max_length=255, blank=True)
    title_en = models.CharField("عنوان انگلیسی", max_length=255, blank=True)
    summary_fa = models.CharField("خلاصه فارسی", max_length=500, blank=True)
    summary_en = models.CharField("خلاصه انگلیسی", max_length=500, blank=True)
    body_fa = models.TextField("متن فارسی", blank=True)
    body_en = models.TextField("متن انگلیسی", blank=True)
    image = models.ImageField("تصویر", upload_to="company/sections/", blank=True, null=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    is_published = models.BooleanField("منتشرشده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "بخش محتوایی شرکت"
        verbose_name_plural = "بخش‌های محتوایی شرکت"

    def __str__(self):
        return self.title_fa or self.get_section_type_display()


class Capability(SourcedContentModel):
    slug = models.SlugField("شناسه نشانی", max_length=255, unique=True)
    title_fa = models.CharField("عنوان فارسی", max_length=255)
    title_en = models.CharField("عنوان انگلیسی", max_length=255, blank=True)
    summary_fa = models.CharField("خلاصه فارسی", max_length=500, blank=True)
    summary_en = models.CharField("خلاصه انگلیسی", max_length=500, blank=True)
    body_fa = models.TextField("توضیحات فارسی", blank=True)
    body_en = models.TextField("توضیحات انگلیسی", blank=True)
    icon = models.CharField("آیکن", max_length=64, blank=True)
    image = models.ImageField("تصویر", upload_to="company/capabilities/", blank=True, null=True)
    cta_label_fa = models.CharField("برچسب اقدام فارسی", max_length=120, blank=True)
    cta_label_en = models.CharField("برچسب اقدام انگلیسی", max_length=120, blank=True)
    cta_url = models.CharField("نشانی اقدام", max_length=500, blank=True)
    seo_title_fa = models.CharField("عنوان سئو فارسی", max_length=255, blank=True)
    seo_title_en = models.CharField("عنوان سئو انگلیسی", max_length=255, blank=True)
    seo_description_fa = models.CharField("توضیح سئو فارسی", max_length=500, blank=True)
    seo_description_en = models.CharField("توضیح سئو انگلیسی", max_length=500, blank=True)
    categories = models.ManyToManyField("catalog.Category", blank=True, related_name="capabilities")
    products = models.ManyToManyField("catalog.Product", blank=True, related_name="capabilities")
    order = models.PositiveSmallIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)
    is_published = models.BooleanField("منتشرشده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "title_fa")
        verbose_name = "توانمندی / خدمت"
        verbose_name_plural = "توانمندی‌ها / خدمات"

    def __str__(self):
        return self.title_fa
