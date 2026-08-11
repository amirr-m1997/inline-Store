from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("carts", "0001_initial")]
    operations = [
        migrations.AlterModelOptions(name="cart", options={"verbose_name": "سبد خرید", "verbose_name_plural": "سبدهای خرید"}),
        migrations.AlterModelOptions(name="cartitem", options={"verbose_name": "آیتم سبد خرید", "verbose_name_plural": "آیتم‌های سبد خرید"}),
    ]
