from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("catalog", "0014_alter_productidentifier_identifier_type")]

    operations = [
        migrations.CreateModel(
            name="ProductFavorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="favorites", to="catalog.product")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="product_favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "پسند محصول", "verbose_name_plural": "پسندهای محصولات"},
        ),
        migrations.CreateModel(
            name="ProductReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rating", models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="امتیاز")),
                ("comment", models.TextField(max_length=3000, verbose_name="نظر")),
                ("is_published", models.BooleanField(default=False, verbose_name="نمایش عمومی")),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="reviews", to="catalog.product")),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="product_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "نظر محصول", "verbose_name_plural": "نظرهای محصولات", "ordering": ("-updated_at", "-id")},
        ),
        migrations.AddConstraint(model_name="productfavorite", constraint=models.UniqueConstraint(fields=("user", "product"), name="catalog_favorite_user_product_unique")),
        migrations.AddIndex(model_name="productfavorite", index=models.Index(fields=["product", "user"], name="cat_favorite_prod_user_idx")),
        migrations.AddConstraint(model_name="productreview", constraint=models.UniqueConstraint(fields=("user", "product"), name="catalog_review_user_product_unique")),
        migrations.AddIndex(model_name="productreview", index=models.Index(fields=["product", "is_published", "-updated_at"], name="catalog_review_public_idx")),
    ]
