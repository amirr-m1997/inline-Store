from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.catalog.models import AttributeDefinition, Category, CategoryAttribute, Product, ProductAttributeValue, ProductIdentifier
from apps.inventory.models import Inventory, Receipt


@override_settings(DEBUG=True)
class CatalogDemoInventoryTests(TestCase):
    def populate(self):
        call_command("populate_demo_content", stdout=StringIO())

    def test_catalog_inventory_demo_data_is_typed_and_idempotent(self):
        self.populate()
        counts = {
            "attributes": AttributeDefinition.objects.filter(code__startswith="demo-").count(),
            "category_attributes": CategoryAttribute.objects.filter(category__code="DEMO-TECHNICAL").count(),
            "products": Product.objects.filter(code__startswith="DEMO-PRODUCT-").count(),
            "identifiers": ProductIdentifier.objects.filter(product__code__startswith="DEMO-PRODUCT-").count(),
            "values": ProductAttributeValue.objects.filter(product__code__startswith="DEMO-PRODUCT-").count(),
            "inventory": Inventory.objects.filter(product__code__startswith="DEMO-PRODUCT-").count(),
            "receipts": Receipt.objects.filter(reference__startswith="demo-content:phase-9.13:receipt:").count(),
        }
        self.populate()
        self.assertEqual(counts["attributes"], AttributeDefinition.objects.filter(code__startswith="demo-").count())
        self.assertEqual(counts["products"], Product.objects.filter(code__startswith="DEMO-PRODUCT-").count())
        self.assertEqual(counts["identifiers"], ProductIdentifier.objects.filter(product__code__startswith="DEMO-PRODUCT-").count())
        self.assertEqual(counts["values"], ProductAttributeValue.objects.filter(product__code__startswith="DEMO-PRODUCT-").count())
        self.assertEqual(counts["inventory"], Inventory.objects.filter(product__code__startswith="DEMO-PRODUCT-").count())
        self.assertEqual(counts["receipts"], Receipt.objects.filter(reference__startswith="demo-content:phase-9.13:receipt:").count())
        self.assertEqual(ProductAttributeValue.objects.get(product__code="DEMO-PRODUCT-001", attribute__code="demo-voltage").number_value, 380)
        self.assertTrue(ProductAttributeValue.objects.get(product__code="DEMO-PRODUCT-001", attribute__code="demo-phase").boolean_value)

    def test_cleanup_removes_only_catalog_demo_records(self):
        real_category = Category.objects.create(code="REAL-CATEGORY", name_fa="دسته واقعی")
        real_product = Product.objects.create(code="REAL-PRODUCT", name="Real product", slug="real-product", category=real_category, unit="عدد")
        self.populate()
        call_command("remove_demo_content", stdout=StringIO())
        self.assertTrue(Product.objects.filter(pk=real_product.pk).exists())
        self.assertFalse(Product.objects.filter(code__startswith="DEMO-PRODUCT-").exists())
        self.assertFalse(AttributeDefinition.objects.filter(code__startswith="demo-").exists())
        self.assertFalse(Receipt.objects.filter(reference__startswith="demo-content:phase-9.13:").exists())

    def test_inventory_admin_changelist_renders(self):
        user_model = get_user_model()
        user_model.objects.create_superuser(username="admin", password="password", email="admin@example.test")
        client = Client()
        self.assertTrue(client.login(username="admin", password="password"))
        response = client.get("/admin/inventory/inventory/")
        self.assertEqual(response.status_code, 200)
