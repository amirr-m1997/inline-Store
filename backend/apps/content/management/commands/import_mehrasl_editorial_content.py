from datetime import datetime, timezone as datetime_timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ContentArticle, ContentCategory
from apps.content.review import IMPORT_MARKER, source_fingerprint


IMPORT_VERSION = "v1"
NEWS_CATEGORY = {"slug": "mehrasl-official-news", "name_fa": "اخبار رسمی مهراصل", "name_en": "Official Mehrasl news"}

NEWS = (
    {
        "slug": "mehrasl-copper-tube-factory-expansion-v1", "title_fa": "بهره‌برداری از فاز توسعه کارخانه لوله مسی مهراصل",
        "source_url": "https://mehrasl.ir/farsi/2025/05/27/%D8%A8%D9%87%D8%B1%D9%87%D8%A8%D8%B1%D8%AF%D8%A7%D8%B1%DB%8C-%D8%A7%D8%B2-%D9%81%D8%A7%D8%B2-%D8%AA%D9%88%D8%B3%D8%B9%D9%87-%DA%A9%D8%A7%D8%B1%D8%AE%D8%A7%D9%86%D9%87-%D9%84%D9%88%D9%84%D9%87/",
        "published_at": datetime(2025, 5, 27, tzinfo=datetime_timezone.utc),
        "body_fa": "فاز توسعه کارخانه لوله مسی شرکت مهراصل در شهرک صنعتی شهید سلیمی تبریز به بهره‌برداری رسید.\n\nاین پروژه صنعتی با سرمایه‌گذاری ۳۰ میلیون دلاری در مدت یک‌ونیم سال اجرا شده و ظرفیت تولید سالانه لوله مسی را از ۱۰ هزار تن به ۳۶ هزار تن افزایش داده است. این طرح همچنین امکان اشتغال مستقیم برای ۴۰۰ نفر را فراهم کرده است.\n\nدر حاشیه این مراسم، تفاهم‌نامه‌ای نیز میان شرکت مهراصل و بانک تجارت برای احداث یک نیروگاه خورشیدی به ظرفیت ۷۶ مگاوات به امضا رسید.",
    },
    {
        "slug": "mehrasl-tejarat-copper-chain-agreement-v1", "title_fa": "بازدید مدیرعامل بانک تجارت از صنایع معدنی و تولیدی مهراصل و امضای تفاهم‌نامه‌های راهبردی برای توسعه زنجیره تولید مس",
        "source_url": "https://mehrasl.ir/farsi/2025/05/27/%D8%A8%D8%A7%D8%B2%D8%AF%DB%8C%D8%AF-%D9%85%D8%AF%DB%8C%D8%B1%D8%B9%D8%A7%D9%85%D9%84-%D8%A8%D8%A7%D9%86%DA%A9-%D8%AA%D8%AC%D8%A7%D8%B1%D8%AA-%D8%A7%D8%B2-%D8%B5%D9%86%D8%A7%DB%8C%D8%B9-%D9%85%D8%B9/",
        "published_at": datetime(2025, 5, 27, tzinfo=datetime_timezone.utc),
        "body_fa": "هادی اخلاقی فیض‌آثار، مدیرعامل بانک تجارت، در جریان بازدید از صنایع معدنی و تولیدی مهراصل، ضمن آشنایی میدانی با آخرین وضعیت اجرای فاز توسعه این مجموعه معدنی، در آئینی رسمی تفاهم‌نامه‌هایی برای اجرای دو طرح بزرگ صنعتی با محوریت احداث کارخانه تولید کاتد مس و نیروگاه خورشیدی به امضا رساند.\n\nاین بازدید و مراسم امضای تفاهم‌نامه‌ها با حضور مدیرکل صنعت، معدن و تجارت استان آذربایجان شرقی برگزار شد.",
    },
    {
        "slug": "mehrasl-east-azerbaijan-industrial-visit-v1", "title_fa": "بازدید استاندار آذربایجان شرقی از کارخانجات تولیدی مهراصل و آشنایی با توانمندی‌های این مجموعه بزرگ صنعتی دانش‌بنیان",
        "source_url": "https://mehrasl.ir/farsi/2024/11/20/sarmast/",
        "published_at": datetime(2024, 11, 20, tzinfo=datetime_timezone.utc),
        "body_fa": "دکتر بهرام سرمست، استاندار آذربایجان شرقی، در ادامه سفر خود به شهرک صنعتی شهید سلیمی، از کارخانجات تولیدی مهراصل بازدید کرد. این بازدید با هدف آشنایی با توانمندی‌های این مجموعه صنعتی و بررسی برنامه‌های توسعه‌ای آن صورت گرفت.\n\nدر جریان این بازدید، خطوط تولید و برنامه‌های توسعه‌ای شرکت در حوزه تهویه مطبوع و تبرید صنعتی بررسی شد و استاندار از فاز توسعه کارخانه لوله مسی مهراصل نیز دیدن کرد.",
    },
)


class Command(BaseCommand):
    help = "Import a conservative, unpublished, source-traceable set of official Mehrasl editorial records."

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = ContentCategory.objects.get_or_create(slug=NEWS_CATEGORY["slug"], defaults={**NEWS_CATEGORY, "is_active": True, "is_published": False, "source_url": "https://mehrasl.ir/farsi/news/", "source_title": "آرشیو خبرهای مهراصل", "migration_notes": f"{IMPORT_MARKER}{IMPORT_VERSION}"})
        created = updated = preserved = 0
        for item in NEWS:
            fingerprint = source_fingerprint(item["title_fa"], item["body_fa"])
            defaults = {**item, "content_type": ContentArticle.ContentType.NEWS, "category": category, "title_en": "", "excerpt_fa": item["title_fa"], "excerpt_en": "", "body_en": "", "is_active": True, "is_published": False, "is_featured": False, "display_order": 0, "review_status": ContentArticle.ReviewStatus.NEEDS_REVIEW, "source_title": item["title_fa"], "migration_notes": f"{IMPORT_MARKER}{IMPORT_VERSION}; official Persian source; English translation intentionally omitted; publication requires business review.", "source_fingerprint": fingerprint}
            record = ContentArticle.objects.filter(source_url=item["source_url"]).first()
            if record is None:
                ContentArticle.objects.create(**defaults)
                created += 1
            elif IMPORT_MARKER in (record.migration_notes or "") and record.source_fingerprint == source_fingerprint(record.title_fa, record.body_fa) == fingerprint:
                record.source_title = item["title_fa"]
                record.save(update_fields=("source_title",))
                updated += 1
            else:
                preserved += 1
        self.stdout.write(self.style.SUCCESS(f"Mehrasl editorial import complete: created={created}, unchanged_imported={updated}, preserved_existing={preserved}, source_records={len(NEWS)}. All records remain unpublished and need review."))
