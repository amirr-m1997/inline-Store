"""Populate conservative, source-traceable first-party company content.

This command is intentionally additive and idempotent.  Records created or
updated by it carry a marker so a later run never overwrites an administrator's
edits.  Sensitive standards/certifications remain unpublished and unverified.
"""

from django.core.management.base import BaseCommand

from apps.company.management.commands.import_mehrasl_content import (
    ABOUT_URL,
    CONTACT_URL,
)
from apps.company.models import Capability, CompanyCertification, CompanyLocation, CompanyMilestone, CompanySection, Industry


MARKER = "initial-content:mehrasl-9.9"
HOME_URL = "https://mehrasl.ir/farsi/"


SECTIONS = (
    {
        "key": "introduction",
        "section_type": "introduction",
        "title_fa": "درباره کارخانجات تولیدی مهراصل",
        "title_en": "About Mehr Asl Manufacturing",
        "summary_fa": "متخصص تهویه مطبوع و تبرید صنعتی",
        "summary_en": "Specialist in air conditioning and industrial refrigeration",
        "body_fa": "شرکت تولیدی مهراصل در سال ۱۳۶۹ با زمینه فعالیت تهویه مطبوع و تبرید صنعتی ثبت و افتتاح شد.",
        "body_en": "Mehr Asl Manufacturing was registered and opened in 1369 with a focus on air conditioning and industrial refrigeration.",
        "source_url": ABOUT_URL,
        "source_title": "درباره ما",
    },
    {
        "key": "production-overview",
        "section_type": "capabilities",
        "title_fa": "تولید و امکانات صنعتی",
        "title_en": "Manufacturing and Industrial Facilities",
        "summary_fa": "تولید تجهیزات تهویه مطبوع و تبرید صنعتی",
        "summary_en": "Manufacturing air-conditioning and industrial refrigeration equipment",
        "body_fa": "منبع رسمی شرکت، تولید چیلر، پکیج یونیت، هواساز، برج خنک‌کننده، تجهیزات تبرید صنعتی و محصولات مسی را در کارخانه‌های مهراصل معرفی می‌کند.",
        "body_en": "The official company source describes production of chillers, packaged units, air handlers, cooling towers, industrial refrigeration equipment and copper products.",
        "source_url": ABOUT_URL,
        "source_title": "درباره ما",
    },
    {
        "key": "product-scope",
        "section_type": "capabilities",
        "title_fa": "دامنه محصولات و فعالیت",
        "title_en": "Product and Activity Scope",
        "summary_fa": "گروه‌های محصولی و صنعتی معرفی‌شده در منبع رسمی",
        "summary_en": "Product and industry groups listed by the official source",
        "body_fa": "فهرست رسمی شرکت گروه‌هایی از ماشین‌آلات راهسازی و معدنی، تجهیزات تهویه و تبرید، محصولات مسی و تجهیزات کاربردی برای صنایع مختلف را معرفی می‌کند.",
        "body_en": "The official product list presents mining and road-construction machinery, air-conditioning and refrigeration equipment, copper products and equipment for several industries.",
        "source_url": HOME_URL,
        "source_title": "صفحه اصلی",
    },
    {
        "key": "sales-network",
        "section_type": "location",
        "title_fa": "دفاتر و مراکز ارائه",
        "title_en": "Offices and Customer Locations",
        "summary_fa": "اطلاعات تماس کارخانه، دفتر فروش و مراکز ارائه رسمی",
        "summary_en": "Official factory, sales-office and customer-location information",
        "body_fa": "صفحات رسمی تماس، کارخانه مرکزی، دفتر فروش مرکزی، نمایشگاه‌ها و فروشگاه مرکزی مهراصل را معرفی می‌کنند.",
        "body_en": "The official contact pages list Mehr Asl's central factory, central sales office, showrooms and central store.",
        "source_url": CONTACT_URL,
        "source_title": "تماس با ما",
    },
)


CAPABILITIES = (
    {
        "slug": "industrial-hvac-refrigeration",
        "title_fa": "تهویه مطبوع و تبرید صنعتی",
        "title_en": "Industrial Air Conditioning and Refrigeration",
        "summary_fa": "تولید محصولات و تجهیزات تهویه مطبوع و تبرید صنعتی.",
        "summary_en": "Manufacturing air-conditioning and industrial refrigeration products and equipment.",
        "body_fa": "منبع رسمی شرکت تهویه مطبوع و تبرید صنعتی را زمینه فعالیت مهراصل معرفی می‌کند و گروه‌هایی مانند چیلر، هواساز، برج خنک‌کننده و تجهیزات تبریدی را فهرست می‌کند.",
        "body_en": "The official source identifies air conditioning and industrial refrigeration as a Mehr Asl activity and lists chillers, air handlers, cooling towers and refrigeration equipment.",
        "seo_title_fa": "تهویه مطبوع و تبرید صنعتی مهراصل",
        "seo_title_en": "Mehr Asl Industrial HVAC and Refrigeration",
        "seo_description_fa": "زمینه فعالیت و گروه‌های محصولی تهویه مطبوع و تبرید صنعتی مهراصل.",
        "seo_description_en": "Mehr Asl's industrial HVAC and refrigeration activity and product groups.",
    },
    {
        "slug": "chiller-manufacturing",
        "title_fa": "تولید چیلر",
        "title_en": "Chiller Manufacturing",
        "summary_fa": "تولید گروه‌های مختلف چیلر معرفی‌شده در فهرست رسمی شرکت.",
        "summary_en": "Manufacturing chiller groups listed by the official company source.",
        "body_fa": "در فهرست رسمی مهراصل، چیلرهای برقی، جذبی، سانتریفیوژ و زیرصفر در گروه محصولات چیلر معرفی شده‌اند.",
        "body_en": "The official Mehr Asl product list includes electric, absorption, centrifugal and low-temperature chiller groups.",
        "seo_title_fa": "تولید چیلر مهراصل",
        "seo_title_en": "Mehr Asl Chiller Manufacturing",
        "seo_description_fa": "گروه‌های چیلر معرفی‌شده در فهرست رسمی محصولات مهراصل.",
        "seo_description_en": "Chiller groups listed in Mehr Asl's official product catalogue.",
    },
    {
        "slug": "heat-exchange-cooling-equipment",
        "title_fa": "تجهیزات تبادل حرارت و سرمایش",
        "title_en": "Heat-Exchange and Cooling Equipment",
        "summary_fa": "تولید مبدل‌های حرارتی، کویل‌ها و تجهیزات سرمایشی معرفی‌شده در منبع رسمی.",
        "summary_en": "Manufacturing heat exchangers, coils and cooling equipment listed by the official source.",
        "body_fa": "فهرست رسمی شرکت مبدل‌های حرارتی، کویل‌ها، رادیاتورهای صنعتی و تجهیزات سرمایشی را در میان گروه‌های تولیدی معرفی می‌کند.",
        "body_en": "The official source lists heat exchangers, coils, industrial radiators and cooling equipment among the company's product groups.",
        "seo_title_fa": "تجهیزات تبادل حرارت و سرمایش مهراصل",
        "seo_title_en": "Mehr Asl Heat-Exchange and Cooling Equipment",
        "seo_description_fa": "گروه تجهیزات تبادل حرارت و سرمایش در محصولات رسمی مهراصل.",
        "seo_description_en": "Mehr Asl's official heat-exchange and cooling equipment groups.",
    },
)


INDUSTRY_TEXT = {
    "mining-road": ("ماشین‌آلات معدنی و راهسازی", "Mining and Road Construction", "گروه محصولات مرتبط با ماشین‌آلات معدنی و راهسازی در فهرست رسمی شرکت."),
    "heavy": ("تجهیزات سنگین", "Heavy Equipment", "گروه تجهیزات سنگین در دسته‌بندی رسمی محصولات شرکت."),
    "industrial-food-petrochemical": ("صنعتی، غذایی و پتروشیمی", "Industrial, Food and Petrochemical", "گروه محصولات معرفی‌شده برای کاربردهای صنعتی، غذایی و پتروشیمی."),
    "hospital": ("بیمارستانی", "Hospital", "گروه محصولات بیمارستانی در دسته‌بندی رسمی محصولات شرکت."),
    "road-rail-air": ("جاده، ریلی و هوایی", "Road, Rail and Air", "گروه تجهیزات معرفی‌شده برای کاربردهای جاده‌ای، ریلی و هوایی."),
    "residential-office-commercial": ("خانگی، اداری و تجاری", "Residential, Office and Commercial", "گروه محصولات معرفی‌شده برای کاربردهای خانگی، اداری و تجاری."),
    "telecom-data-center": ("مخابرات و دیتاسنتر", "Telecom and Data Center", "گروه تجهیزات سرمایش و تهویه معرفی‌شده برای مخابرات و دیتاسنتر."),
}


def _has_marker(value):
    return MARKER in (value or "")


def _mark(value, note):
    if _has_marker(value):
        return value
    return f"{value}\n{MARKER}: {note}".strip()


def _fill(instance, values, note):
    """Fill only empty fields, then mark the record as managed by this seed."""
    for field, value in values.items():
        if value and not getattr(instance, field, None):
            setattr(instance, field, value)
    instance.migration_notes = _mark(getattr(instance, "migration_notes", ""), note)
    instance.save()
    return instance


class Command(BaseCommand):
    help = "Populate conservative, source-traceable initial Mehrasl company content."

    def handle(self, *args, **options):
        counts = {"sections": 0, "locations": 0, "milestones": 0, "industries": 0, "capabilities": 0}

        for data in SECTIONS:
            key = data["key"]
            values = {field: value for field, value in data.items() if field != "key"}
            item = CompanySection.objects.filter(migration_notes__contains=f"{MARKER}: section:{key}").first()
            if item is None:
                item = CompanySection.objects.filter(section_type=values["section_type"], title_fa=values["title_fa"]).first()
            if item is None:
                item = CompanySection.objects.create(**values, order=len(CompanySection.objects.all()))
                was_managed = False
            else:
                was_managed = _has_marker(item.migration_notes)
            if item is not None and not was_managed and item.pk and not _has_marker(item.migration_notes):
                _fill(item, values, f"section:{key}")
            if not was_managed and (not item.is_published or not item.is_active):
                item.is_published = True
                item.is_active = True
                item.migration_notes = _mark(item.migration_notes, f"section:{key}")
                item.save(update_fields=("is_published", "is_active", "migration_notes"))
            counts["sections"] += 1

        publish_locations = {"central-factories", "electric-chiller-factory", "central-sales-office", "central-showroom", "tabriz-showroom", "central-store"}
        location_names = {
            "central-factories": "کارخانجات مرکزی مهراصل",
            "electric-chiller-factory": "کارخانه تولید چیلرهای برقی",
            "central-sales-office": "دفتر فروش مرکزی مهراصل",
            "central-showroom": "نمایشگاه مرکزی مهراصل",
            "tabriz-showroom": "نمایشگاه تبریز مهراصل – دانشسرا",
            "central-store": "فروشگاه مرکزی مهراصل",
            "aria-factory": "کارخانجات برودتی آریا",
        }
        for key, name in location_names.items():
            item = CompanyLocation.objects.filter(name_fa=name).first()
            if item is None:
                continue
            was_managed = _has_marker(item.migration_notes)
            if not was_managed:
                _fill(item, {}, f"location:{key}")
            if key in publish_locations and not was_managed:
                item.is_published = True
                item.verification_required = False
                item.save(update_fields=("is_published", "verification_required"))
            counts["locations"] += 1

        milestone = CompanyMilestone.objects.filter(title_fa="ثبت و افتتاح شرکت مهراصل").first()
        if milestone:
            was_managed = _has_marker(milestone.migration_notes)
            if not was_managed:
                _fill(milestone, {"description_fa": "ثبت و افتتاح شرکت مهراصل در سال ۱۳۶۹.", "source_url": ABOUT_URL, "source_title": "درباره ما"}, "milestone:1369")
                milestone.is_published = True
                milestone.verification_required = False
                milestone.save(update_fields=("is_published", "verification_required"))
            counts["milestones"] += 1

        for item in Industry.objects.filter(slug__in=tuple(INDUSTRY_TEXT)):
            fa, en, description = INDUSTRY_TEXT[item.slug]
            values = {"name_fa": fa, "name_en": en, "description_fa": description, "description_en": description, "source_url": HOME_URL, "source_title": "صفحه اصلی", "is_active": True, "is_published": True}
            if not _has_marker(item.migration_notes):
                _fill(item, values, f"industry:{item.slug}; English wording is provisional and requires editorial approval.")
                item.is_active = True
                item.is_published = True
                item.save(update_fields=("is_active", "is_published"))
            counts["industries"] += 1

        for data in CAPABILITIES:
            item = Capability.objects.filter(slug=data["slug"]).first()
            if item is None:
                item = Capability.objects.create(**{key: value for key, value in data.items()}, source_url=ABOUT_URL, source_title="درباره ما", is_active=True, is_published=True, migration_notes=f"{MARKER}: capability:{data['slug']}; English wording is provisional and requires editorial approval.")
            elif not _has_marker(item.migration_notes):
                _fill(item, {**data, "source_url": ABOUT_URL, "source_title": "درباره ما"}, f"capability:{data['slug']}; English wording is provisional and requires editorial approval.")
                item.is_active = True
                item.is_published = True
                item.save(update_fields=("is_active", "is_published"))
            counts["capabilities"] += 1

        self.stdout.write(self.style.SUCCESS(f"Initial Mehrasl company content populated idempotently: {counts}. Certifications remain unpublished and verification-gated."))
