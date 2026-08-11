from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_product_technical_specs")]
    operations = [
        migrations.AlterModelOptions(name="category", options={"ordering": ("parent_id", "code"), "verbose_name": "دسته‌بندی", "verbose_name_plural": "دسته‌بندی‌ها"}),
        migrations.AlterModelOptions(name="product", options={"ordering": ("name",), "verbose_name": "محصول", "verbose_name_plural": "محصولات"}),
        migrations.AlterModelOptions(name="productimage", options={"ordering": ("sort_order", "id"), "verbose_name": "تصویر محصول", "verbose_name_plural": "تصاویر محصولات"}),
    ]
