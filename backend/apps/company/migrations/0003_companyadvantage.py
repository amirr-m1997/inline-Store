from django.db import migrations, models


def seed_advantages(apps, schema_editor):
    CompanyAdvantage = apps.get_model("company", "CompanyAdvantage")
    items = [
        ("تأمین مستقیم محصولات صنعتی", "دسترسی به تجهیزات و قطعات موردنیاز تولید", "✓", 10),
        ("تضمین کیفیت کالا", "کنترل کیفیت و اصالت محصولات", "✓", 20),
        ("ارسال سریع سفارشات", "پیگیری و ارسال هماهنگ سفارش‌های سازمانی", "✓", 30),
        ("پشتیبانی فنی تخصصی", "همراهی کارشناسان در انتخاب محصول", "✓", 40),
    ]
    for title_fa, description_fa, icon, order in items:
        CompanyAdvantage.objects.update_or_create(title_fa=title_fa, defaults={"description_fa": description_fa, "icon": icon, "order": order, "is_active": True})


class Migration(migrations.Migration):
    dependencies = [("company", "0002_companyinfo_hero_settings")]
    operations = [
        migrations.CreateModel(
            name="CompanyAdvantage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title_fa", models.CharField(max_length=255, verbose_name="عنوان فارسی")),
                ("title_en", models.CharField(blank=True, max_length=255, verbose_name="عنوان انگلیسی")),
                ("description_fa", models.CharField(blank=True, max_length=255, verbose_name="توضیح فارسی")),
                ("description_en", models.CharField(blank=True, max_length=255, verbose_name="توضیح انگلیسی")),
                ("icon", models.CharField(blank=True, max_length=64, verbose_name="آیکن")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "مزیت شرکت", "verbose_name_plural": "مزیت‌های شرکت"},
        ),
        migrations.RunPython(seed_advantages, migrations.RunPython.noop),
    ]
