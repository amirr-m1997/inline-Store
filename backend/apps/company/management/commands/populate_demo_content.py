"""Create clearly marked development content for visual/admin testing."""

from pathlib import Path
from django.core.files import File

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from decimal import Decimal

from apps.catalog.models import (
    AttributeDefinition,
    Category,
    CategoryAttribute,
    Product,
    ProductAttributeValue,
    ProductBrand,
    ProductDocument,
    ProductIdentifier,
    normalize_identifier,
)
from apps.company.models import Capability, CompanyCertification, CompanyHonor, CompanyLocation, CompanyMilestone, CompanySection, Industry
from apps.inventory.models import Inventory, Receipt
from apps.website.models import CustomerFeedback, CustomerSupportRequest, WarrantyPolicy, WarrantyRegistration


MARKER = "demo-content:phase-9.10"
CATALOG_MARKER = "demo-content:phase-9.13"
DEMO_SOURCE = "https://example.invalid/demo/phase-9.10"


class Command(BaseCommand):
    help = "Populate development-only demo company/catalog content."

    def add_arguments(self, parser):
        parser.add_argument("--allow-production", action="store_true", help="Allow demo records when DEBUG is disabled.")

    def _note(self, value=""):
        return f"{value}\n{MARKER}".strip()

    def _get_or_create_sourced(self, model, lookup, defaults):
        item = model.objects.filter(**lookup).first()
        if item is None:
            item = model.objects.create(**defaults, migration_notes=self._note(defaults.get("migration_notes", "")))
            return item, True
        if MARKER not in (getattr(item, "migration_notes", "") or ""):
            return item, False
        return item, False

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError("Demo content is disabled when DEBUG=False. Use --allow-production only for an explicit non-production review.")

        counts = {"sections": 0, "locations": 0, "milestones": 0, "industries": 0, "capabilities": 0, "certifications": 0, "honors": 0, "brands": 0, "documents": 0, "categories": 0, "products": 0, "attributes": 0, "category_attributes": 0, "identifiers": 0, "attribute_values": 0, "inventory": 0, "receipts": 0, "support": 0}
        self._sections(counts)
        self._locations(counts)
        self._milestones(counts)
        self._industries(counts)
        self._capabilities(counts)
        self._certifications(counts)
        self._honors(counts)
        self._brands(counts)
        self._catalog_inventory(counts)
        self._support(counts)
        document_note = self._documents(counts)
        self.stdout.write(self.style.SUCCESS(f"Demo content populated safely: {counts}. {document_note}"))

    def _support(self, counts):
        policy, created = WarrantyPolicy.objects.get_or_create(title_fa="[DEMO] اطلاعات ثبت گارانتی", defaults={"title_en":"[DEMO] Warranty registration information", "body_fa":"محتوای نمونه محیط توسعه است و شرایط واقعی گارانتی محسوب نمی‌شود.", "body_en":"Development sample only; this is not a warranty term.", "registration_enabled":True, "is_published":True, "migration_notes":self._note("support-policy; demo only")})
        counts["support"] += int(created)
        if not CustomerSupportRequest.objects.filter(subject="[DEMO] درخواست پشتیبانی").exists(): CustomerSupportRequest.objects.create(full_name="[DEMO] Customer", phone="09120000001", subject="[DEMO] درخواست پشتیبانی", message="Development fixture", request_type="other"); counts["support"]+=1
        if not WarrantyRegistration.objects.filter(full_name="[DEMO] Customer").exists(): WarrantyRegistration.objects.create(full_name="[DEMO] Customer", phone="09120000001", notes="Development fixture"); counts["support"]+=1
        if not CustomerFeedback.objects.filter(message="[DEMO] Development feedback").exists(): CustomerFeedback.objects.create(feedback_type="other", rating=5, message="[DEMO] Development feedback"); counts["support"]+=1

    def _sections(self, counts):
        records = (
            ("demo-introduction", "introduction", "[DEMO] Company introduction", "[DEMO] معرفی شرکت", "A short development-only introduction used to preview the About layout.", "این متن نمونه صرفاً برای بررسی چیدمان صفحه معرفی است.", "about"),
            ("demo-manufacturing", "capabilities", "[DEMO] Manufacturing overview", "[DEMO] نمای کلی تولید", "A neutral multi-paragraph demo section for manufacturing content.", "این بخش نمونه برای نمایش محتوای چندپاراگرافی در محیط توسعه است.\n\nاین ادعا اطلاعات رسمی شرکت نیست.", "about"),
            ("demo-quality", "value", "[DEMO] Quality approach", "[DEMO] رویکرد کیفیت", "Demo content showing a concise supporting section.", "محتوای آزمایشی رویکرد کیفیت.", "about"),
            ("demo-network", "location", "[DEMO] Sales and support network", "[DEMO] شبکه فروش و پشتیبانی", "Demo content with a longer summary to test responsive wrapping and cards.", "محتوای نمونه برای آزمون نمایش شبکه فروش و پشتیبانی.", "contact"),
            ("demo-expertise", "history", "[DEMO] Industrial expertise", "[DEMO] تخصص صنعتی", "Development-only content for section hierarchy testing.", "محتوای نمونه برای تست سلسله‌مراتب بخش‌های صنعتی.", "about"),
        )
        for order, (key, section_type, title_en, title_fa, summary_en, summary_fa, source_title) in enumerate(records, 20):
            if CompanySection.objects.filter(migration_notes__contains=f"{MARKER}:section:{key}").exists():
                continue
            if CompanySection.objects.filter(title_fa=title_fa).exists():
                continue
            CompanySection.objects.create(
                section_type=section_type, title_fa=title_fa, title_en=title_en,
                summary_fa=summary_fa, summary_en=summary_en,
                body_fa=summary_fa, body_en=summary_en, order=order,
                is_active=True, is_published=True, source_url=DEMO_SOURCE,
                source_title=f"Development demo: {source_title}",
                migration_notes=self._note(f"section:{key}; development-only content; not official company wording."),
            )
            counts["sections"] += 1

    def _locations(self, counts):
        records = (
            ("factory", "[DEMO] Factory campus", "[DEMO] شهرک کارخانه نمونه", "Demo address line, industrial district", "۰۲۱-۰۰۰۰۰۰۰۱", "demo.factory@example.invalid", "09:00–17:00"),
            ("office", "[DEMO] Sales office", "[DEMO] دفتر فروش نمونه", "Demo office address", "۰۲۱-۰۰۰۰۰۰۰۲", "", ""),
            ("showroom", "[DEMO] Showroom", "[DEMO] نمایشگاه نمونه", "Demo showroom address", "", "demo.showroom@example.invalid", "Saturday–Wednesday"),
            ("store", "[DEMO] Parts store", "[DEMO] فروشگاه قطعات نمونه", "Demo store address", "", "", ""),
            ("representative", "[DEMO] Representative", "[DEMO] نمایندگی نمونه", "Demo representative address", "۰۲۱-۰۰۰۰۰۰۰۵", "demo.rep@example.invalid", "By appointment"),
        )
        for order, (location_type, name_en, name_fa, address, phone, email, hours) in enumerate(records, 20):
            if CompanyLocation.objects.filter(migration_notes__contains=f"{MARKER}:location:{location_type}").exists() or CompanyLocation.objects.filter(name_fa=name_fa).exists():
                continue
            CompanyLocation.objects.create(location_type=location_type, name_fa=name_fa, name_en=name_en, address_fa=address, phone=phone, email=email, working_hours=hours, order=order, is_active=True, is_published=True, verification_required=False, source_url=DEMO_SOURCE, source_title="Development demo location", migration_notes=self._note(f"location:{location_type}; development-only content; not an official location."))
            counts["locations"] += 1

    def _milestones(self, counts):
        records = (("1995", "[DEMO] Early development", "[DEMO] شروع توسعه"), ("2008", "[DEMO] Product expansion", "[DEMO] گسترش محصولات"), ("2024", "[DEMO] Digital catalog", "[DEMO] کاتالوگ دیجیتال"))
        for order, (year, title_en, title_fa) in enumerate(records, 20):
            key = year
            if CompanyMilestone.objects.filter(migration_notes__contains=f"{MARKER}:milestone:{key}").exists() or CompanyMilestone.objects.filter(title_fa=title_fa).exists():
                continue
            CompanyMilestone.objects.create(date_label=year, title_fa=title_fa, title_en=title_en, description_fa="رویداد نمونه برای نمایش تایم‌لاین در محیط توسعه.", description_en="A demo milestone for development timeline previews.", order=order, is_published=True, verification_required=False, source_url=DEMO_SOURCE, source_title="Development demo timeline", migration_notes=self._note(f"milestone:{key}; development-only content."))
            counts["milestones"] += 1

    def _industries(self, counts):
        records = (("demo-mining", "[DEMO] Mining applications", "[DEMO] کاربردهای معدنی", "A demo industry description with no inferred relationships."), ("demo-commercial", "[DEMO] Commercial facilities", "[DEMO] تأسیسات تجاری", "A second demo industry used to preview an empty relationship state."))
        for order, (slug, name_en, name_fa, description) in enumerate(records, 20):
            if Industry.objects.filter(slug=slug).exists():
                continue
            Industry.objects.create(slug=slug, name_fa=name_fa, name_en=name_en, description_fa=description, description_en=description, source_url=DEMO_SOURCE, source_title="Development demo industry", migration_notes=self._note(f"industry:{slug}; development-only content; no official relationship implied."), order=order, is_active=True, is_published=True)
            counts["industries"] += 1

    def _capabilities(self, counts):
        records = (("demo-design", "[DEMO] Systems design", "[DEMO] طراحی سیستم", "Short demo summary.", "A longer demo body used to test capability detail layouts."), ("demo-maintenance", "[DEMO] Maintenance support", "[DEMO] پشتیبانی نگهداری", "A medium-length demo summary for cards.", "Development-only maintenance support copy; it is not a company service claim."), ("demo-engineering", "[DEMO] Engineering review", "[DEMO] بررسی مهندسی", "Demo engineering summary.", "Demo engineering body with no real-world promise."), ("demo-documentation", "[DEMO] Technical documentation", "[DEMO] مستندسازی فنی", "Demo documentation summary.", "Demo content for testing links and SEO fields."), ("demo-long", "[DEMO] Long capability title for responsive testing", "[DEMO] عنوان طولانی توانمندی برای آزمون واکنش‌گرایی", "A deliberately longer summary to test wrapping.", "This multi-paragraph demo body exists only to exercise the storefront presentation and admin editing experience."))
        for order, (slug, title_en, title_fa, summary_en, body_en) in enumerate(records, 20):
            if Capability.objects.filter(slug=slug).exists():
                continue
            Capability.objects.create(slug=slug, title_fa=title_fa, title_en=title_en, summary_fa=summary_en, summary_en=summary_en, body_fa=body_en, body_en=body_en, cta_label_fa="مشاهده نمونه", cta_label_en="View demo", cta_url="/demo-content", seo_title_fa=title_fa, seo_title_en=title_en, seo_description_fa=summary_en, seo_description_en=summary_en, order=order, is_active=True, is_published=True, source_url=DEMO_SOURCE, source_title="Development demo capability", migration_notes=self._note(f"capability:{slug}; development-only content; not an official service claim."))
            counts["capabilities"] += 1

    def _certifications(self, counts):
        records = (("[DEMO] Verified-looking certificate", "[DEMO] گواهی نمونه تأییدشده", "verified", True, "DEMO-VERIFIED-001"), ("[DEMO] Draft certificate", "[DEMO] گواهی نمونه پیش‌نویس", "unverified", False, "DEMO-DRAFT-001"), ("[DEMO] Certificate with metadata", "[DEMO] گواهی نمونه با فراداده", "pending", False, "DEMO-PENDING-001"))
        for order, (title_en, title_fa, status, published, code) in enumerate(records, 20):
            if CompanyCertification.objects.filter(certificate_code=code).exists():
                continue
            CompanyCertification.objects.create(title_fa=title_fa, title_en=title_en, issuer="[DEMO] Development issuer", certificate_code=code, verification_status=status, is_published=published, order=order, source_url=DEMO_SOURCE, source_title="Development demo certification", migration_notes=self._note(f"certification:{code}; never a real certification or validity claim."))
            counts["certifications"] += 1

    def _honors(self, counts):
        for order, year in enumerate(("2018", "2022"), 20):
            title_fa = f"[DEMO] افتخار نمونه {year}"
            if CompanyHonor.objects.filter(year_label=year, title_fa=title_fa).exists():
                continue
            CompanyHonor.objects.create(title_fa=title_fa, title_en=f"[DEMO] Sample honor {year}", issuer="[DEMO] Development organization", year_label=year, description_fa="رکورد نمونه برای نمایش افتخارات؛ ادعای واقعی نیست.", description_en="A development-only honor record; not a real claim.", is_published=True, verification_required=False, order=order, source_url=DEMO_SOURCE, source_title="Development demo honor", migration_notes=self._note(f"honor:{year}; never a real award claim."))
            counts["honors"] += 1

    def _brands(self, counts):
        for slug, name in (("demo-industrial-brand-a", "Demo Industrial Brand A"), ("demo-industrial-brand-b", "Demo Industrial Brand B"), ("demo-long-brand-name", "Demo Industrial Brand with a Longer Name") ):
            if ProductBrand.objects.filter(slug=slug).exists() or ProductBrand.objects.filter(name=name).exists():
                continue
            ProductBrand.objects.create(name=name, code=f"DEMO-{slug[-1].upper()}", slug=slug, description_fa="برند نمونه برای محیط توسعه؛ سازنده یا شریک واقعی نیست.", description_en="Development-only brand; not a real manufacturer or partner.", is_active=True, is_published=True, seo_title_fa=name, seo_title_en=name, seo_description_fa="برند نمونه توسعه", seo_description_en="Development demo brand")
            counts["brands"] += 1

    def _documents(self, counts):
        product = Product.objects.filter(code__startswith="DEMO-PRODUCT-").order_by("id").first()
        fixture_dir = Path(settings.MEDIA_ROOT) / "product-documents"
        fixtures = sorted(path for path in fixture_dir.rglob("*.pdf") if not path.name.lower().startswith(("inv", "invoice"))) if fixture_dir.exists() else []
        if product is None or not fixtures:
            return "No safe local product-document fixture/product was available; demo documents skipped."
        fixture = str(fixtures[0].relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
        records = (("datasheet", "[DEMO] Datasheet", "دیتاشیت نمونه"), ("manual", "[DEMO] Manual", "راهنمای نمونه"), ("certificate", "[DEMO] Certificate", "گواهی نمونه"))
        for order, (document_type, title_en, title_fa) in enumerate(records, 20):
            display_name = f"[DEMO] {document_type}-{product.pk}.pdf"
            if ProductDocument.objects.filter(display_name=display_name).exists():
                continue
            with (settings.MEDIA_ROOT / fixture).open("rb") as source:
                ProductDocument.objects.create(product=product, document_type=document_type, title_fa=title_fa, title_en=title_en, file=File(source, name=Path(fixture).name), display_name=display_name, language="en/fa", revision="DEMO-1", display_order=order, is_active=True, is_published=True)
            counts["documents"] += 1
        return f"Created demo documents from safe fixture {fixture}. CAD was skipped because no safe CAD fixture exists."

    def _catalog_inventory(self, counts):
        """Create isolated catalog records so demo attributes never affect real products."""
        category, created = Category.objects.get_or_create(
            code="DEMO-TECHNICAL",
            defaults={"name_fa": "[DEMO] تجهیزات فنی", "name_en": "[DEMO] Technical equipment", "is_active": True},
        )
        if created:
            counts["categories"] += 1
        products = []
        for code, name_fa, name_en, unit in (
            ("DEMO-PRODUCT-001", "[DEMO] چیلر نمونه", "[DEMO] Chiller example", "دستگاه"),
            ("DEMO-PRODUCT-002", "[DEMO] مبدل حرارتی نمونه", "[DEMO] Heat exchanger example", "دستگاه"),
            ("DEMO-PRODUCT-TEST", "محصول تست", "Test Product", "عدد"),
        ):
            product, created = Product.objects.get_or_create(
                code=code,
                defaults={"name": name_fa, "slug": "test-product" if code == "DEMO-PRODUCT-TEST" else code.lower(), "category": category, "unit": unit, "is_active": True},
            )
            if created:
                counts["products"] += 1
            products.append(product)

        definitions = (
            ("demo-voltage", "[DEMO] ولتاژ", "[DEMO] Voltage", "number", "V", True, True),
            ("demo-power", "[DEMO] توان", "[DEMO] Power", "number", "kW", True, True),
            ("demo-material", "[DEMO] جنس", "[DEMO] Material", "text", "", True, False),
            ("demo-phase", "[DEMO] فاز", "[DEMO] Phase", "boolean", "", True, True),
            ("demo-installation-type", "[DEMO] نوع نصب", "[DEMO] Installation type", "enum", "", False, False),
        )
        attrs = {}
        for order, (code, name_fa, name_en, value_type, unit, filterable, comparable) in enumerate(definitions, 20):
            attribute, created = AttributeDefinition.objects.get_or_create(
                code=code,
                defaults={"name_fa": name_fa, "name_en": name_en, "value_type": value_type, "unit": unit, "is_filterable": filterable, "is_comparable": comparable, "display_order": order, "is_active": True},
            )
            if created:
                counts["attributes"] += 1
            attrs[code] = attribute
            relation, relation_created = CategoryAttribute.objects.get_or_create(
                category=category,
                attribute=attribute,
                defaults={"is_required": code in {"demo-voltage", "demo-power"}, "is_filterable": filterable, "display_order": order, "unit_override": unit},
            )
            if relation_created:
                counts["category_attributes"] += 1

        values = (
            ("demo-voltage", {"number_value": Decimal("380")}),
            ("demo-power", {"number_value": Decimal("15")}),
            ("demo-material", {"text_value": "Steel"}),
            ("demo-phase", {"boolean_value": True}),
            ("demo-installation-type", {"enum_value": "floor"}),
        )
        for product in products:
            for code, fields in values:
                value, created = ProductAttributeValue.objects.get_or_create(product=product, attribute=attrs[code], defaults=fields)
                if created:
                    counts["attribute_values"] += 1
        for product_index, product in enumerate(products, 1):
            mpn = "DEMO-MPN-CH-100" if product.code == "DEMO-PRODUCT-TEST" else f"DEMO-MPN-CH-{100 + product_index}"
            for identifier_type, display in (
                (ProductIdentifier.Type.INTERNAL_CODE, f"DEMO-INTERNAL-{product_index:03d}"),
                (ProductIdentifier.Type.SKU, f"DEMO-SKU-{product_index:03d}"),
                (ProductIdentifier.Type.MANUFACTURER_PART_NUMBER, mpn),
                (ProductIdentifier.Type.BARCODE, f"DEMO-BARCODE-{product_index:012d}"),
                (ProductIdentifier.Type.ALIAS, f"demo-alias-{product_index}"),
            ):
                identifier, created = ProductIdentifier.objects.get_or_create(
                    product=product,
                    identifier_type=identifier_type,
                    normalized_value=normalize_identifier(display),
                    defaults={"display_value": display},
                )
                if created:
                    counts["identifiers"] += 1
        for index, product in enumerate(products, 1):
            inventory, created = Inventory.objects.get_or_create(product=product, defaults={"on_hand_quantity": 25 - index * 5, "reserved_quantity": index})
            if created:
                counts["inventory"] += 1
            reference = f"{CATALOG_MARKER}:receipt:{product.code}"
            receipt, created = Receipt.objects.get_or_create(product=product, reference=reference, defaults={"quantity": 25 - index * 5, "occurred_at": timezone.now()})
            if created:
                counts["receipts"] += 1
