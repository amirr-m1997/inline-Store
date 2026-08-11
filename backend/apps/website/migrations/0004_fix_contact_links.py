from django.db import migrations


def fix_contact_links(apps, schema_editor):
    SiteNavigation = apps.get_model("website", "SiteNavigation")
    FooterLink = apps.get_model("website", "FooterLink")
    SiteNavigation.objects.filter(url__in=("/fa#contact", "/fa/about#contact")).update(url="/fa/contact")
    FooterLink.objects.filter(url__in=("/fa#contact", "/fa/about#contact")).update(url="/fa/contact")


def reverse_contact_links(apps, schema_editor):
    SiteNavigation = apps.get_model("website", "SiteNavigation")
    FooterLink = apps.get_model("website", "FooterLink")
    SiteNavigation.objects.filter(title_fa="تماس با ما", url="/fa/contact").update(url="/fa#contact")
    FooterLink.objects.filter(title_fa="تماس با ما", url="/fa/contact").update(url="/fa/about#contact")


class Migration(migrations.Migration):
    dependencies = [("website", "0003_contactmessage")]
    operations = [migrations.RunPython(fix_contact_links, reverse_contact_links)]
