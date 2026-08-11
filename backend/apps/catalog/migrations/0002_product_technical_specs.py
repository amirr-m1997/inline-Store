from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.AddField(model_name="product", name="technical_specs", field=models.JSONField(blank=True, default=dict))]
