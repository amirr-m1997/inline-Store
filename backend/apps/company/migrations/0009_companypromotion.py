from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("company", "0008_companybanner")]

    operations = [
        migrations.CreateModel(
            name="CompanyPromotion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title_fa", models.CharField(max_length=255, verbose_name="عنوان فارسی")),
                ("title_en", models.CharField(blank=True, max_length=255, verbose_name="عنوان انگلیسی")),
                ("description_fa", models.TextField(blank=True, verbose_name="توضیحات فارسی")),
                ("description_en", models.TextField(blank=True, verbose_name="توضیحات انگلیسی")),
                ("discount_percentage", models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="درصد تخفیف")),
                ("image", models.ImageField(blank=True, null=True, upload_to="company/promotions/", verbose_name="تصویر تبلیغ")),
                ("button_text_fa", models.CharField(blank=True, max_length=100, verbose_name="متن دکمه فارسی")),
                ("button_text_en", models.CharField(blank=True, max_length=100, verbose_name="متن دکمه انگلیسی")),
                ("button_url", models.CharField(blank=True, max_length=255, verbose_name="نشانی دکمه")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("company_info", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="promotions", to="company.companyinfo", verbose_name="اطلاعات شرکت")),
            ],
            options={"verbose_name": "تبلیغ ویژه فروشگاه", "verbose_name_plural": "تبلیغات ویژه فروشگاه", "ordering": ("order", "id")},
        ),
    ]
