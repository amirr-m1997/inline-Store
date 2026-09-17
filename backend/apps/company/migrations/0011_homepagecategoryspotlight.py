from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0017_productquestion"), ("company", "0010_companypromotion_placement_and_type")]

    operations = [
        migrations.CreateModel(
            name="HomepageCategorySpotlight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title_fa", models.CharField(blank=True, max_length=255, verbose_name="عنوان فارسی (اختیاری)")),
                ("title_en", models.CharField(blank=True, max_length=255, verbose_name="عنوان انگلیسی (اختیاری)")),
                ("description_fa", models.CharField(blank=True, max_length=500, verbose_name="توضیح فارسی")),
                ("description_en", models.CharField(blank=True, max_length=500, verbose_name="توضیح انگلیسی")),
                ("image", models.ImageField(blank=True, null=True, upload_to="company/category-spotlights/", verbose_name="تصویر دسته")),
                ("button_text_fa", models.CharField(blank=True, max_length=100, verbose_name="متن دکمه فارسی")),
                ("button_text_en", models.CharField(blank=True, max_length=100, verbose_name="متن دکمه انگلیسی")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="homepage_spotlights", to="catalog.category", verbose_name="دسته‌بندی")),
                ("company_info", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="category_spotlights", to="company.companyinfo", verbose_name="اطلاعات شرکت")),
            ],
            options={"verbose_name": "دسته‌بندی برجسته صفحه اصلی", "verbose_name_plural": "دسته‌بندی‌های برجسته صفحه اصلی", "ordering": ("order", "id")},
        ),
    ]
