from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("company", "0012_homepagecategoryspotlight_placement")]

    operations = [
        migrations.AlterField(
            model_name="homepagecategoryspotlight",
            name="placement",
            field=models.CharField(
                choices=[
                    ("after_featured", "بعد از محصولات منتخب"),
                    ("after_best_sellers", "بعد از پرفروش‌ترین‌ها"),
                    ("between_newest_discounts", "بین جدیدترین‌ها و تخفیف‌ها"),
                    ("after_discounts", "بعد از بیشترین تخفیف‌ها"),
                    ("after_low_stock", "بعد از محصولات در حال اتمام"),
                ],
                default="after_featured",
                max_length=32,
                verbose_name="جایگاه نمایش",
            ),
        ),
    ]
