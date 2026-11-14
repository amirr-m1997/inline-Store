from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0018_category_image")]

    operations = [
        migrations.AddField(model_name="product", name="is_obsolete", field=models.BooleanField(db_index=True, default=False, verbose_name="کالای منسوخ (عدم نمایش عمومی)")),
        migrations.AddField(model_name="product", name="replacement_product", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="replaces", to="catalog.product", verbose_name="کالای جایگزین")),
    ]
