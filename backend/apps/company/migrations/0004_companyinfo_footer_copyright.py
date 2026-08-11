from django.db import migrations, models


def seed_copyright(apps, schema_editor):
    CompanyInfo = apps.get_model("company", "CompanyInfo")
    for company in CompanyInfo.objects.filter(footer_copyright_fa=""):
        company.footer_copyright_fa = f"تمام حقوق برای {company.name_fa} محفوظ است."
        company.save(update_fields=["footer_copyright_fa"])


class Migration(migrations.Migration):
    dependencies = [("company", "0003_companyadvantage")]
    operations = [
        migrations.AddField(model_name="companyinfo", name="footer_copyright_fa", field=models.CharField(blank=True, max_length=500, verbose_name="متن کپی‌رایت فارسی")),
        migrations.AddField(model_name="companyinfo", name="footer_copyright_en", field=models.CharField(blank=True, max_length=500, verbose_name="متن کپی‌رایت انگلیسی")),
        migrations.RunPython(seed_copyright, migrations.RunPython.noop),
    ]
