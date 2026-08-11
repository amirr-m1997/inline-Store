from django.db import migrations, models


def seed_hero_settings(apps, schema_editor):
    CompanyInfo = apps.get_model("company", "CompanyInfo")
    company = CompanyInfo.objects.first()
    if company:
        company.hero_title_fa = company.name_fa
        company.hero_slogan_fa = "تأمین‌کننده محصولات و تجهیزات صنعتی"
        company.hero_description_fa = company.description
        company.save(update_fields=("hero_title_fa", "hero_slogan_fa", "hero_description_fa"))


class Migration(migrations.Migration):
    dependencies = [("company", "0001_initial")]
    operations = [
        migrations.AddField(model_name="companyinfo", name="hero_created_at", field=models.DateTimeField(auto_now_add=True, verbose_name="ایجاد هیرو")),
        migrations.AddField(model_name="companyinfo", name="hero_description_en", field=models.TextField(blank=True, verbose_name="توضیحات هیرو انگلیسی")),
        migrations.AddField(model_name="companyinfo", name="hero_description_fa", field=models.TextField(blank=True, verbose_name="توضیحات هیرو فارسی")),
        migrations.AddField(model_name="companyinfo", name="hero_image", field=models.ImageField(blank=True, null=True, upload_to="company/hero/", verbose_name="تصویر هیرو")),
        migrations.AddField(model_name="companyinfo", name="hero_is_active", field=models.BooleanField(default=True, verbose_name="فعال بودن هیرو")),
        migrations.AddField(model_name="companyinfo", name="hero_slogan_en", field=models.CharField(blank=True, max_length=255, verbose_name="شعار هیرو انگلیسی")),
        migrations.AddField(model_name="companyinfo", name="hero_slogan_fa", field=models.CharField(blank=True, max_length=255, verbose_name="شعار هیرو فارسی")),
        migrations.AddField(model_name="companyinfo", name="hero_title_en", field=models.CharField(blank=True, max_length=255, verbose_name="عنوان هیرو انگلیسی")),
        migrations.AddField(model_name="companyinfo", name="hero_title_fa", field=models.CharField(blank=True, max_length=255, verbose_name="عنوان هیرو فارسی")),
        migrations.AddField(model_name="companyinfo", name="hero_updated_at", field=models.DateTimeField(auto_now=True, verbose_name="به‌روزرسانی هیرو")),
        migrations.AddField(model_name="companyinfo", name="mobile_hero_image", field=models.ImageField(blank=True, null=True, upload_to="company/hero/", verbose_name="تصویر موبایل هیرو")),
        migrations.AddField(model_name="companyinfo", name="primary_button_link", field=models.CharField(blank=True, max_length=255, verbose_name="لینک دکمه اصلی")),
        migrations.AddField(model_name="companyinfo", name="primary_button_text", field=models.CharField(blank=True, max_length=100, verbose_name="متن دکمه اصلی")),
        migrations.AddField(model_name="companyinfo", name="secondary_button_link", field=models.CharField(blank=True, max_length=255, verbose_name="لینک دکمه دوم")),
        migrations.AddField(model_name="companyinfo", name="secondary_button_text", field=models.CharField(blank=True, max_length=100, verbose_name="متن دکمه دوم")),
        migrations.RunPython(seed_hero_settings, migrations.RunPython.noop),
    ]
