from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import AttributeDefinition, Category, CategoryAttribute, Product, ProductAttributeValue, ProductBrand, ProductIdentifier


class CatalogDataModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="fasteners", name_fa="اتصالات", slug="fasteners")
        self.product = Product.objects.create(code="BOLT-001", name="Bolt", slug="bolt-001", category=self.category, unit="piece", technical_specs={"diameter": "10 mm"})

    def test_existing_product_and_legacy_specs_remain_valid(self):
        self.product.refresh_from_db()
        self.assertIsNone(self.product.brand)
        self.assertEqual(self.product.technical_specs, {"diameter": "10 mm"})

    def test_product_brand_is_optional_and_assignable(self):
        brand = ProductBrand.objects.create(name="Acme", code="ACME")
        self.product.brand = brand
        self.product.save()
        self.assertEqual(self.product.brand, brand)

    def test_identifier_normalizes_without_changing_display_value(self):
        identifier = ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.MANUFACTURER_PART_NUMBER, display_value=" ab- 12 ")
        self.assertEqual(identifier.normalized_value, "ab- 12")
        self.assertEqual(identifier.display_value, " ab- 12 ")

    def test_non_alias_identifiers_are_globally_unique_but_aliases_are_not(self):
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.SKU, display_value="SKU-1")
        second = Product.objects.create(code="BOLT-002", name="Bolt 2", slug="bolt-002", category=self.category, unit="piece")
        with self.assertRaises(ValidationError):
            ProductIdentifier.objects.create(product=second, identifier_type=ProductIdentifier.Type.SKU, display_value="sku-1")
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.ALIAS, display_value="common alias")
        ProductIdentifier.objects.create(product=second, identifier_type=ProductIdentifier.Type.ALIAS, display_value="COMMON ALIAS")

    def test_typed_attribute_value_requires_matching_value_type(self):
        diameter = AttributeDefinition.objects.create(code="diameter", name_fa="قطر", value_type=AttributeDefinition.ValueType.NUMBER, unit="mm", is_filterable=True, is_comparable=True)
        CategoryAttribute.objects.create(category=self.category, attribute=diameter, is_required=True, is_filterable=True, display_order=2, unit_override="mm")
        value = ProductAttributeValue.objects.create(product=self.product, attribute=diameter, number_value="10.5")
        self.assertEqual(str(value.number_value), "10.5")
        with self.assertRaises(ValidationError):
            ProductAttributeValue.objects.create(product=self.product, attribute=diameter, text_value="ten")

    def test_category_attribute_relationship_is_unique_and_ordered(self):
        material = AttributeDefinition.objects.create(code="material", name_fa="جنس", value_type=AttributeDefinition.ValueType.ENUM)
        setting = CategoryAttribute.objects.create(category=self.category, attribute=material, display_order=3, is_filterable=True)
        self.assertEqual(self.category.attribute_settings.get(), setting)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CategoryAttribute.objects.create(category=self.category, attribute=material)


class CatalogRichTextSanitizerTests(TestCase):
    def test_allows_word_like_rich_text_markup(self):
        from apps.catalog.serializers import rich_text_to_html
        html = "<h2>عنوان</h2><p><strong>متن</strong> با <a href=\"https://example.com\">لینک</a> و <em>کج</em></p><ul><li>مورد</li></ul>"
        self.assertEqual(rich_text_to_html(html), html)

    def test_strips_scripts_and_event_handler_attributes(self):
        from apps.catalog.serializers import rich_text_to_html
        html = '<p onclick="alert(1)">متن</p><script>alert(2)</script><iframe src="https://evil.example"></iframe><img src="x" onerror="alert(3)">'
        cleaned = rich_text_to_html(html)
        self.assertNotIn("script", cleaned)
        self.assertNotIn("iframe", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("onerror", cleaned)


class CatalogListShortDescriptionTests(TestCase):
    def test_list_exposes_plain_text_short_description(self):
        category = Category.objects.create(code="fasteners", name_fa="اتصالات", slug="fasteners")
        Product.objects.create(code="BOLT-010", name="Bolt", slug="bolt-010", category=category, unit="piece", description="<h2>عنوان</h2><p>پیچ آلن خشکه با گرید <strong>12.9</strong> مناسب اتصالات صنعتی سنگین.</p>")
        response = self.client.get("/api/v1/products/?search=BOLT-010")
        self.assertEqual(response.status_code, 200)
        item = next((row for row in response.json()["results"] if row["code"] == "BOLT-010"), None)
        self.assertIsNotNone(item)
        self.assertIn("short_description", item)
        self.assertNotIn("<", item["short_description"])
        self.assertIn("12.9", item["short_description"])

    def test_short_description_is_truncated_and_empty_safe(self):
        category = Category.objects.create(code="pipes", name_fa="لوله", slug="pipes")
        Product.objects.create(code="PIPE-001", name="Pipe", slug="pipe-001", category=category, unit="meter", description="<p>" + "لوله " * 100 + "</p>")
        Product.objects.create(code="PIPE-002", name="Bare", slug="pipe-002", category=category, unit="meter", description="")
        response = self.client.get("/api/v1/products/?search=PIPE-00")
        self.assertEqual(response.status_code, 200)
        by_code = {row["code"]: row for row in response.json()["results"]}
        self.assertLessEqual(len(by_code["PIPE-001"]["short_description"]), 161)
        self.assertEqual(by_code["PIPE-002"]["short_description"], "")
