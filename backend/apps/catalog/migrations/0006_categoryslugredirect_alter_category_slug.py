from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_alter_category_slug")]
    operations = [
        migrations.AlterField(
            model_name="category", name="slug",
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
        migrations.CreateModel(
            name="CategorySlugRedirect",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("old_slug", models.SlugField(max_length=255, unique=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="slug_redirects", to="catalog.category")),
            ],
            options={"ordering": ("old_slug",), "verbose_name": "نشانی قدیمی دسته‌بندی", "verbose_name_plural": "نشانی‌های قدیمی دسته‌بندی"},
        ),
    ]
