from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_productimage_localized_alt")]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(max_length=255, unique=True),
        ),
    ]
