from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0012_productdocument")]

    operations = [
        migrations.AlterField(
            model_name="productdocument",
            name="document_type",
            field=models.CharField(
                choices=[
                    ("datasheet", "دیتاشیت"),
                    ("manual", "راهنما"),
                    ("cad", "CAD"),
                    ("certificate", "گواهی‌نامه"),
                    ("catalogue", "کاتالوگ"),
                    ("other", "سایر"),
                ],
                max_length=16,
            ),
        ),
    ]
