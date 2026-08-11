from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_authentication_completion")]
    operations = [
        migrations.AddField(model_name="user", name="customer_type", field=models.CharField(choices=[("personal", "شخصی"), ("business", "حقوقی")], default="personal", max_length=16)),
        migrations.AddField(model_name="user", name="economic_code", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name="user", name="job_title", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="user", name="landline", field=models.CharField(blank=True, max_length=32)),
        migrations.CreateModel(name="CustomerAddress", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=100, verbose_name="عنوان نشانی")), ("recipient_name", models.CharField(max_length=255, verbose_name="نام تحویل‌گیرنده")), ("recipient_phone", models.CharField(max_length=16, verbose_name="شماره تحویل‌گیرنده")), ("province", models.CharField(max_length=100, verbose_name="استان")), ("city", models.CharField(max_length=100, verbose_name="شهر")), ("postal_code", models.CharField(blank=True, max_length=20, verbose_name="کدپستی")), ("address", models.TextField(verbose_name="نشانی")), ("is_default", models.BooleanField(default=False, verbose_name="نشانی پیش‌فرض")), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delivery_addresses", to="accounts.user")),
        ], options={"ordering": ("-is_default", "id"), "verbose_name": "نشانی مشتری", "verbose_name_plural": "نشانی‌های مشتری"}),
    ]
