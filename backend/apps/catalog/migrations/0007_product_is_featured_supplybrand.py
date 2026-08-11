from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_categoryslugredirect_alter_category_slug")]
    operations = [
        migrations.AddField(
            model_name="product", name="is_featured",
            field=models.BooleanField(db_index=True, default=False, verbose_name="نمایش در محصولات منتخب"),
        ),
        migrations.CreateModel(
            name="SupplyBrand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="نام برند")),
                ("logo", models.ImageField(blank=True, null=True, upload_to="brands/", verbose_name="لوگو")),
                ("website", models.URLField(blank=True, verbose_name="وب‌سایت")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
            ],
            options={"ordering": ("order", "name"), "verbose_name": "برند قابل تأمین", "verbose_name_plural": "برندهای قابل تأمین"},
        ),
    ]
