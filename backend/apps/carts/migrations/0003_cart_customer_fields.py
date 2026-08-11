from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("carts", "0002_alter_cart_options_alter_cartitem_options")]
    operations = [
        migrations.AddField(model_name="cart", name="customer_first_name", field=models.CharField(blank=True, max_length=150)),
        migrations.AddField(model_name="cart", name="customer_last_name", field=models.CharField(blank=True, max_length=150)),
        migrations.AddField(model_name="cart", name="customer_email", field=models.EmailField(blank=True, max_length=254)),
        migrations.AddField(model_name="cart", name="customer_phone", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name="cart", name="customer_company_name", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="cart", name="customer_national_id", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name="cart", name="shipping_province", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="cart", name="shipping_city", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="cart", name="shipping_postal_code", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="cart", name="shipping_address", field=models.TextField(blank=True)),
    ]
