import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("catalog", "0001_initial")]
    operations = [
        migrations.CreateModel(name="CurrencyRate", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("currency", models.CharField(choices=[("IRR", "Iranian Rial"), ("USD", "US Dollar")], max_length=3)), ("rate_to_irr", models.DecimalField(decimal_places=4, max_digits=18)), ("rate_date", models.DateField()), ("source", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True))]),
        migrations.CreateModel(name="ProductPrice", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("amount", models.DecimalField(decimal_places=2, max_digits=18)), ("currency", models.CharField(choices=[("IRR", "Iranian Rial"), ("USD", "US Dollar")], max_length=3)), ("effective_from", models.DateTimeField()), ("effective_to", models.DateTimeField(blank=True, null=True)), ("source", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)), ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prices", to="catalog.product"))]),
        migrations.AddConstraint(model_name="currencyrate", constraint=models.UniqueConstraint(fields=("currency", "rate_date"), name="currency_rate_per_date_unique")), migrations.AddIndex(model_name="productprice", index=models.Index(fields=["product", "effective_from"], name="pricing_pro_product_1c2236_idx")),
    ]
