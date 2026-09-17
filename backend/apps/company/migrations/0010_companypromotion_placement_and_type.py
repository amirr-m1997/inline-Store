from django.db import migrations, models


def add_default_home_promotions(apps, schema_editor):
    CompanyInfo = apps.get_model("company", "CompanyInfo")
    CompanyPromotion = apps.get_model("company", "CompanyPromotion")
    company = CompanyInfo.objects.first()
    if company is None:
        return

    defaults = (
        ("home_middle", "campaign", "انتخاب فنی، خرید مطمئن", "برای انتخاب تجهیزات، تیم مهراصل در کنار پروژه شماست.", "دریافت مشاوره", "/fa/contact/"),
        ("home_bottom", "brand", "برندهای معتبر، تأمین یکپارچه", "برندهای قابل تأمین را برای پروژه خود بررسی کنید.", "مشاهده برندها", "/fa/brands/"),
    )
    for order, (placement, promotion_type, title, description, button_text, button_url) in enumerate(defaults, start=1):
        if not CompanyPromotion.objects.filter(company_info=company, placement=placement).exists():
            CompanyPromotion.objects.create(
                company_info=company,
                placement=placement,
                promotion_type=promotion_type,
                title_fa=title,
                description_fa=description,
                button_text_fa=button_text,
                button_url=button_url,
                order=order,
                is_active=True,
            )


class Migration(migrations.Migration):
    dependencies = [("company", "0009_companypromotion")]

    operations = [
        migrations.AddField(
            model_name="companypromotion",
            name="placement",
            field=models.CharField(choices=[("featured", "کنار محصولات منتخب"), ("home_middle", "میانه صفحه اصلی"), ("home_bottom", "پایین صفحه اصلی")], default="featured", max_length=20, verbose_name="جایگاه نمایش"),
        ),
        migrations.AddField(
            model_name="companypromotion",
            name="promotion_type",
            field=models.CharField(choices=[("campaign", "کمپین و خدمات شرکت"), ("product", "تبلیغ محصول"), ("brand", "تبلیغ برند")], default="campaign", max_length=20, verbose_name="نوع تبلیغ"),
        ),
        migrations.RunPython(add_default_home_promotions, migrations.RunPython.noop),
    ]
