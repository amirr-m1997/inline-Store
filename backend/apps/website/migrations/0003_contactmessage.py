from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("website", "0002_footer_models")]

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=255, verbose_name="نام و نام خانوادگی")),
                ("phone", models.CharField(max_length=64, verbose_name="شماره تماس")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="ایمیل")),
                ("subject", models.CharField(max_length=255, verbose_name="موضوع")),
                ("message", models.TextField(max_length=5000, verbose_name="پیام")),
                ("status", models.CharField(choices=[("new", "جدید"), ("in_progress", "در حال بررسی"), ("resolved", "پاسخ داده شده")], default="new", max_length=16, verbose_name="وضعیت")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
            ],
            options={"verbose_name": "پیام تماس", "verbose_name_plural": "پیام‌های تماس", "ordering": ("-created_at",)},
        ),
    ]
