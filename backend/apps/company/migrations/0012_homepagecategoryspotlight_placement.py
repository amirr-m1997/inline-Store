from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("company", "0011_homepagecategoryspotlight")]

    operations = [
        migrations.AddField(
            model_name="homepagecategoryspotlight",
            name="placement",
            field=models.CharField(
                choices=[
                    ("after_featured", "بعد از محصولات منتخب"),
                    ("between_newest_discounts", "بین جدیدترین‌ها و تخفیف‌ها"),
                    ("after_discounts", "بعد از بیشترین تخفیف‌ها"),
                ],
                default="after_featured",
                max_length=32,
                verbose_name="جایگاه نمایش",
            ),
        ),
    ]
