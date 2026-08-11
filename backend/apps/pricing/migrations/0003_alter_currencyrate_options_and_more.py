from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("pricing", "0002_productprice_discount_percentage")]
    operations = [
        migrations.AlterModelOptions(name="currencyrate", options={"verbose_name": "نرخ ارز", "verbose_name_plural": "نرخ‌های ارز"}),
        migrations.AlterModelOptions(name="productprice", options={"verbose_name": "قیمت محصول", "verbose_name_plural": "قیمت محصولات"}),
    ]
