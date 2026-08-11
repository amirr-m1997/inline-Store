from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_alter_category_options_alter_product_options_and_more")]
    operations = [
        migrations.AddField(model_name="productimage", name="alt_fa", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="productimage", name="alt_en", field=models.CharField(blank=True, max_length=255)),
    ]
