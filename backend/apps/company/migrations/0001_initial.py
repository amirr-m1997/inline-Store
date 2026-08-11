from django.db import migrations, models


def create_demo_company(apps, schema_editor):
    CompanyInfo = apps.get_model("company", "CompanyInfo")
    CompanyInfo.objects.get_or_create(
        id=1,
        defaults={"name_fa": "شرکت تولیدی مهر اصل"},
    )


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CompanyInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name_fa", models.CharField(max_length=255, verbose_name="نام فارسی شرکت")),
                ("logo", models.ImageField(blank=True, null=True, upload_to="company/", verbose_name="لوگو")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                ("address", models.TextField(blank=True, verbose_name="نشانی")),
                ("phone", models.CharField(blank=True, max_length=64, verbose_name="تلفن")),
                ("mobile", models.CharField(blank=True, max_length=64, verbose_name="موبایل")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="ایمیل")),
                ("website", models.URLField(blank=True, verbose_name="وب‌سایت")),
                ("working_hours", models.CharField(blank=True, max_length=255, verbose_name="ساعات کاری")),
            ],
            options={"verbose_name": "اطلاعات شرکت", "verbose_name_plural": "اطلاعات شرکت"},
        ),
        migrations.RunPython(create_demo_company, migrations.RunPython.noop),
    ]
