from django.core.management.base import BaseCommand

from apps.company.models import CompanyCertification, CompanyLocation, CompanyMilestone, Industry


ABOUT_URL = "https://mehrasl.ir/farsi/about-us/"
CONTACT_URL = "https://mehrasl.ir/farsi/main-manufacturing-corporation/"
SALES_URL = "https://mehrasl.ir/farsi/central-sales-office/"
SHOWROOM_URL = "https://mehrasl.ir/farsi/contact-us-main-showroom-mehrasl/"
TABRIZ_SHOWROOM_URL = "https://mehrasl.ir/farsi/daneshsaramehrasl/"


LOCATIONS = [
    {"key": "central-factories", "location_type": "factory", "name_fa": "کارخانجات مرکزی مهراصل", "address_fa": "تبریز، کیلومتر ۳۵ جاده آذرشهر، شهرک صنعتی شهید سلیمی", "phone": "۳۴۳۲۸۹۴۱-۰۴۱", "email": "fmo3@mehrasl.ir", "source_url": CONTACT_URL, "source_title": "تماس با ما (کارخانجات مرکزی شرکت مهراصل)"},
    {"key": "electric-chiller-factory", "location_type": "factory", "name_fa": "کارخانه تولید چیلرهای برقی", "address_fa": "سی‌متری اول شهرک شهید سلیمی، تبریز", "source_url": ABOUT_URL, "source_title": "درباره ما", "migration_notes": "آدرس از معرفی کارخانه‌ها برداشت شده و جزئیات تماس جداگانه در منبع بررسی نشده است."},
    {"key": "aria-factory", "location_type": "factory", "name_fa": "کارخانجات برودتی آریا", "address_fa": "سی‌متری اول شهرک شهید سلیمی، تبریز", "source_url": ABOUT_URL, "source_title": "درباره ما", "migration_notes": "به‌عنوان زیرمجموعه در منبع معرفی شده؛ نیازمند تأیید رابطه سازمانی پیش از انتشار."},
    {"key": "central-sales-office", "location_type": "office", "name_fa": "دفتر فروش مرکزی مهراصل", "address_fa": "تهران، خیابان مفتح شمالی، خیابان زهره، شماره ۱۷", "phone": "۸۸۳۰۰۸۰۱-۰۲۱", "email": "sales.manager@mehrasl.ir", "source_url": SALES_URL, "source_title": "تماس با ما (دفتر فروش مرکزی شرکت مهراصل)"},
    {"key": "central-showroom", "location_type": "showroom", "name_fa": "نمایشگاه مرکزی مهراصل", "address_fa": "تهران، خیابان مفتح جنوبی، پلاک ۹۲", "phone": "۸۸۳۰۳۸۱۲-۰۲۱", "source_url": SHOWROOM_URL, "source_title": "تماس با ما (نمایشگاه مرکزی شرکت مهراصل)"},
    {"key": "tabriz-showroom", "location_type": "showroom", "name_fa": "نمایشگاه تبریز مهراصل – دانشسرا", "address_fa": "تبریز، خیابان دانشسرا، دفتر نمایشگاه مهراصل", "phone": "۰۰۹۸۲۱۸۳۶۴", "source_url": TABRIZ_SHOWROOM_URL, "source_title": "تماس با ما (نمایشگاه تبریز شرکت مهراصل – دانشسرا)"},
    {"key": "central-store", "location_type": "store", "name_fa": "فروشگاه مرکزی مهراصل", "address_fa": "تهران، خیابان مفتح جنوبی، پایین‌تر از چهارراه سمیه، پلاک ۱۵۲", "source_url": ABOUT_URL, "source_title": "درباره ما", "migration_notes": "آدرس فروشگاه از متن معرفی شرکت برداشت شده و جزئیات تماس جداگانه در منبع بررسی نشده است."},
]

INDUSTRIES = [
    ("mining-road", "معدنی و راهسازی", "The source explicitly lists road-construction and mining machinery."),
    ("heavy", "سنگین", "The source uses a separate heavy-equipment/product grouping."),
    ("industrial-food-petrochemical", "صنعتی، غذایی و پتروشیمی", "Explicit source navigation grouping."),
    ("hospital", "بیمارستانی", "Explicit source navigation grouping."),
    ("road-rail-air", "جاده، ریلی و هوایی", "Explicit source navigation grouping."),
    ("residential-office-commercial", "خانگی، اداری و تجاری", "Explicit source navigation grouping."),
    ("telecom-data-center", "مخابرات و دیتاسنتر", "Explicit source navigation grouping."),
]


class Command(BaseCommand):
    help = "Import authoritative Mehrasl company content as unpublished, source-traceable draft records."

    def handle(self, *args, **options):
        created = {"locations": 0, "milestones": 0, "certifications": 0, "industries": 0}
        for source_item in LOCATIONS:
            item = {key: value for key, value in source_item.items() if key != "key"}
            _, was_created = CompanyLocation.objects.update_or_create(name_fa=item["name_fa"], defaults={**item, "is_published": False, "verification_required": True})
            created["locations"] += int(was_created)
        _, was_created = CompanyMilestone.objects.update_or_create(title_fa="ثبت و افتتاح شرکت مهراصل", defaults={"date_label": "۱۳۶۹", "description_fa": "منبع رسمی ثبت و افتتاح شرکت را در سال ۱۳۶۹ ذکر می‌کند.", "source_url": ABOUT_URL, "source_title": "درباره ما", "migration_notes": "تاریخ در تقویم منبع فارسی است؛ تبدیل تقویمی انجام نشده است.", "is_published": False, "verification_required": True})
        created["milestones"] += int(was_created)
        for title, code in (("ISO 9000", "ISO 9000"), ("ISO 14000", "ISO 14000"), ("ASTM B280", "ASTM B280"), ("ISO 5151 / ISIRI 6016", "ISO 5151 / ISIRI 6016"), ("ARI 440 / ISIRI 3740", "ARI 440 / ISIRI 3740"), ("ARI 590", "ARI 590")):
            _, was_created = CompanyCertification.objects.update_or_create(certificate_code=code, defaults={"title_fa": title, "source_url": ABOUT_URL, "source_title": "درباره ما", "verification_status": "unverified", "is_published": False})
            created["certifications"] += int(was_created)
        for slug, name, note in INDUSTRIES:
            _, was_created = Industry.objects.update_or_create(slug=slug, defaults={"name_fa": name, "source_url": "https://mehrasl.ir/farsi/", "source_title": "صفحه اصلی", "migration_notes": note, "is_published": False})
            created["industries"] += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Mehrasl import complete; created {created}. Existing records were preserved and all imported records remain unpublished."))
