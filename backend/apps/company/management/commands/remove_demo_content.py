from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import AttributeDefinition, Category, CategoryAttribute, Product, ProductAttributeValue, ProductBrand, ProductDocument, ProductIdentifier
from apps.company.models import Capability, CompanyCertification, CompanyHonor, CompanyLocation, CompanyMilestone, CompanySection, Industry
from apps.inventory.models import Inventory, Receipt
from apps.website.models import CustomerFeedback, CustomerSupportRequest, WarrantyPolicy, WarrantyRegistration


MARKER = "demo-content:phase-9.10"
CATALOG_MARKER = "demo-content:phase-9.13"


class Command(BaseCommand):
    help = "Remove only Phase 9.10/9.13 development demo records."

    @transaction.atomic
    def handle(self, *args, **options):
        counts = {}
        counts["WarrantyPolicy"] = WarrantyPolicy.objects.filter(migration_notes__contains=MARKER).delete()[0]
        counts["WarrantyRegistration"] = WarrantyRegistration.objects.filter(full_name="[DEMO] Customer").delete()[0]
        counts["CustomerSupportRequest"] = CustomerSupportRequest.objects.filter(subject="[DEMO] درخواست پشتیبانی").delete()[0]
        counts["CustomerFeedback"] = CustomerFeedback.objects.filter(message="[DEMO] Development feedback").delete()[0]
        for model in (CompanySection, CompanyLocation, CompanyMilestone, CompanyCertification, CompanyHonor, Industry, Capability):
            deleted, _ = model.objects.filter(migration_notes__contains=MARKER).delete()
            counts[model.__name__] = deleted
        deleted, _ = ProductBrand.objects.filter(name__startswith="Demo Industrial Brand").delete()
        counts["ProductBrand"] = deleted
        deleted, _ = ProductDocument.objects.filter(display_name__startswith="[DEMO]").delete()
        counts["ProductDocument"] = deleted
        demo_products = list(Product.objects.filter(code__startswith="DEMO-PRODUCT-"))
        demo_product_ids = [product.pk for product in demo_products]
        if demo_product_ids:
            deleted, _ = Receipt.objects.filter(product_id__in=demo_product_ids, reference__startswith=f"{CATALOG_MARKER}:receipt:").delete()
            counts["Receipt"] = deleted
            deleted, _ = Inventory.objects.filter(product_id__in=demo_product_ids).delete()
            counts["Inventory"] = deleted
            deleted, _ = ProductAttributeValue.objects.filter(product_id__in=demo_product_ids).delete()
            counts["ProductAttributeValue"] = deleted
            deleted, _ = ProductIdentifier.objects.filter(product_id__in=demo_product_ids).delete()
            counts["ProductIdentifier"] = deleted
            deleted, _ = Product.objects.filter(pk__in=demo_product_ids).delete()
            counts["Product"] = deleted
        demo_attributes = list(AttributeDefinition.objects.filter(code__in=("demo-voltage", "demo-power", "demo-material", "demo-phase", "demo-installation-type")))
        if demo_attributes:
            deleted, _ = CategoryAttribute.objects.filter(attribute_id__in=[attribute.pk for attribute in demo_attributes]).delete()
            counts["CategoryAttribute"] = deleted
            deleted, _ = AttributeDefinition.objects.filter(pk__in=[attribute.pk for attribute in demo_attributes]).delete()
            counts["AttributeDefinition"] = deleted
        deleted, _ = Category.objects.filter(code="DEMO-TECHNICAL").delete()
        counts["Category"] = deleted
        self.stdout.write(self.style.SUCCESS(f"Removed only development demo records: {counts}. Stored files were not deleted."))
