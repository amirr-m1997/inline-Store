from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.AddField(model_name="user", name="address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="user", name="company_name", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="user", name="phone", field=models.CharField(blank=True, max_length=32)),
    ]
