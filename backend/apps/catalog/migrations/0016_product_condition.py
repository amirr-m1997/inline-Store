from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0015_productfavorite_productreview")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="condition",
            field=models.CharField(choices=[("new", "نو"), ("used", "کارکرده")], db_index=True, default="new", max_length=12, verbose_name="وضعیت کالا"),
        ),
    ]
