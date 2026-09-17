from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("catalog", "0016_product_condition")]

    operations = [
        migrations.CreateModel(
            name="ProductQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("question", models.TextField(max_length=1500, verbose_name="پرسش")),
                ("answer", models.TextField(blank=True, max_length=3000, verbose_name="پاسخ مدیر")),
                ("is_published", models.BooleanField(default=False, verbose_name="نمایش عمومی")),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="questions", to="catalog.product")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="product_questions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "پرسش محصول", "verbose_name_plural": "پرسش‌ها و پاسخ‌های محصولات", "ordering": ("-updated_at", "-id")},
        ),
        migrations.AddIndex(model_name="productquestion", index=models.Index(fields=["product", "is_published", "-updated_at"], name="catalog_question_public_idx")),
    ]
