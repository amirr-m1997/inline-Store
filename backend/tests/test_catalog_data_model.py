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
