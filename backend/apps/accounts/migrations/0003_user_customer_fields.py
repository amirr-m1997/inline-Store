from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_profile_fields")]
    operations = [
        migrations.AddField(model_name="user", name="national_id", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(model_name="user", name="province", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="user", name="city", field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name="user", name="postal_code", field=models.CharField(blank=True, max_length=20)),
    ]
