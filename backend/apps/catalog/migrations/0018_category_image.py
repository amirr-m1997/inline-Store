from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0017_productquestion"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="catalog/categories/", verbose_name="تصویر دسته‌بندی"),
        ),
    ]
