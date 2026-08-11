from django.db import migrations, models


def seed_navigation(apps, schema_editor):
    SiteNavigation = apps.get_model("website", "SiteNavigation")
    items = [
        ("صفحه اصلی", "/fa", 10),
        ("دسته‌بندی محصولات", "/fa/category/search", 20),
        ("جدیدترین محصولات", "/fa/category/search?ordering=-created_at", 30),
        ("محصولات تخفیف‌دار", "/fa/category/search?discount=true", 40),
        ("درباره ما", "/fa/about", 50),
        ("تماس با ما", "/fa#contact", 60),
    ]
    for title_fa, url, order in items:
        SiteNavigation.objects.update_or_create(url=url, defaults={"title_fa": title_fa, "order": order, "is_active": True})


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="SiteNavigation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title_fa", models.CharField(max_length=100, verbose_name="عنوان فارسی")),
                ("title_en", models.CharField(blank=True, max_length=100, verbose_name="عنوان انگلیسی")),
                ("url", models.CharField(max_length=255, verbose_name="نشانی")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("icon", models.CharField(blank=True, max_length=64, verbose_name="آیکن")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("order", "id"), "verbose_name": "ناوبری وب‌سایت", "verbose_name_plural": "ناوبری وب‌سایت"},
        ),
        migrations.RunPython(seed_navigation, migrations.RunPython.noop),
    ]
