from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]
    operations = [
        migrations.AlterModelOptions(name="inventory", options={"verbose_name": "موجودی انبار", "verbose_name_plural": "موجودی‌های انبار"}),
        migrations.AlterModelOptions(name="issue", options={"ordering": ("-occurred_at",), "verbose_name": "حواله خروج", "verbose_name_plural": "حواله‌های خروج"}),
        migrations.AlterModelOptions(name="receipt", options={"ordering": ("-occurred_at",), "verbose_name": "رسید انبار", "verbose_name_plural": "رسیدهای انبار"}),
        migrations.AlterModelOptions(name="reservation", options={"verbose_name": "رزرو موجودی", "verbose_name_plural": "رزروهای موجودی"}),
    ]
