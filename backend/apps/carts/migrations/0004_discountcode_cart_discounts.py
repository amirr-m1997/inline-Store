from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("carts", "0003_cart_customer_fields")]
    operations = [
        migrations.CreateModel(name="DiscountCode", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("code", models.CharField(max_length=64, unique=True, verbose_name="کد تخفیف")), ("percentage", models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0.01), django.core.validators.MaxValueValidator(100)], verbose_name="درصد تخفیف")), ("minimum_order_amount", models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="حداقل مبلغ سفارش (ریال)")), ("valid_from", models.DateTimeField(verbose_name="شروع اعتبار")), ("valid_until", models.DateTimeField(blank=True, null=True, verbose_name="پایان اعتبار")), ("max_uses", models.PositiveIntegerField(blank=True, null=True, verbose_name="حداکثر دفعات استفاده")), ("usage_count", models.PositiveIntegerField(default=0, editable=False, verbose_name="دفعات استفاده‌شده")), ("is_active", models.BooleanField(default=True, verbose_name="فعال")), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering": ("-created_at",), "verbose_name": "کد تخفیف", "verbose_name_plural": "کدهای تخفیف"}),
        migrations.AddField(model_name="cart", name="discount_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=18)),
        migrations.AddField(model_name="cart", name="discount_percentage", field=models.DecimalField(decimal_places=2, default=0, max_digits=5)),
        migrations.AddField(model_name="cart", name="final_total", field=models.DecimalField(decimal_places=2, default=0, max_digits=18)),
        migrations.AddField(model_name="cart", name="discount_code", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="carts", to="carts.discountcode")),
    ]
