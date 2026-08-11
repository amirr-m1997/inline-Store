from django.db import migrations, models
import django.db.models.deletion


def seed_footer(apps, schema_editor):
    FooterSection = apps.get_model("website", "FooterSection")
    FooterLink = apps.get_model("website", "FooterLink")
    content = [
        ("فروشگاه", 10, [("دسته‌بندی محصولات", "/fa/categories", 10), ("جدیدترین محصولات", "/fa/category/search?ordering=-created_at", 20), ("محصولات تخفیف‌دار", "/fa/category/search?discount=true", 30)]),
        ("شرکت", 20, [("درباره ما", "/fa/about", 10), ("تماس با ما", "/fa/about#contact", 20)]),
        ("پشتیبانی", 30, [("حساب کاربری", "/fa/account", 10), ("سبد خرید", "/fa/cart", 20)]),
    ]
    for title, order, links in content:
        section, _ = FooterSection.objects.get_or_create(title_fa=title, defaults={"order": order, "is_active": True})
        for link_title, url, link_order in links:
            FooterLink.objects.get_or_create(section=section, url=url, defaults={"title_fa": link_title, "order": link_order, "is_active": True})


class Migration(migrations.Migration):
    dependencies = [("website", "0001_initial")]
    operations = [
        migrations.CreateModel(name="FooterSection", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title_fa", models.CharField(max_length=100, verbose_name="عنوان فارسی")), ("title_en", models.CharField(blank=True, max_length=100, verbose_name="عنوان انگلیسی")), ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")), ("is_active", models.BooleanField(default=True, verbose_name="فعال"))], options={"ordering": ("order", "id"), "verbose_name": "بخش فوتر", "verbose_name_plural": "بخش‌های فوتر"}),
        migrations.CreateModel(name="TrustBadge", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title_fa", models.CharField(max_length=100, verbose_name="عنوان فارسی")), ("title_en", models.CharField(blank=True, max_length=100, verbose_name="عنوان انگلیسی")), ("image", models.ImageField(blank=True, null=True, upload_to="footer/trust-badges/", verbose_name="تصویر نشان")), ("url", models.URLField(blank=True, verbose_name="نشانی مقصد")), ("alt_fa", models.CharField(blank=True, max_length=255, verbose_name="متن جایگزین فارسی")), ("alt_en", models.CharField(blank=True, max_length=255, verbose_name="متن جایگزین انگلیسی")), ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")), ("is_active", models.BooleanField(default=True, verbose_name="فعال"))], options={"ordering": ("order", "id"), "verbose_name": "نشان اعتماد", "verbose_name_plural": "نشان‌های اعتماد"}),
        migrations.CreateModel(name="FooterLink", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title_fa", models.CharField(max_length=100, verbose_name="عنوان فارسی")), ("title_en", models.CharField(blank=True, max_length=100, verbose_name="عنوان انگلیسی")), ("url", models.CharField(max_length=500, verbose_name="نشانی")), ("order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")), ("is_active", models.BooleanField(default=True, verbose_name="فعال")), ("open_in_new_tab", models.BooleanField(default=False, verbose_name="باز شدن در صفحه جدید")), ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="links", to="website.footersection", verbose_name="بخش"))], options={"ordering": ("order", "id"), "verbose_name": "پیوند فوتر", "verbose_name_plural": "پیوندهای فوتر"}),
        migrations.RunPython(seed_footer, migrations.RunPython.noop),
    ]
