from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import AttributeDefinition, Category, CategoryAttribute, Product, ProductAttributeValue, ProductBrand, ProductIdentifier
from apps.catalog.search_normalization import normalize_search_text
from apps.pricing.models import ProductPrice
from django.utils import timezone


class CatalogFacetedQueryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="tools", name_fa="ابزار", slug="tools")
        self.brand = ProductBrand.objects.create(name="Industrial Co", code="IND")
        self.material = AttributeDefinition.objects.create(code="material", name_fa="جنس", value_type=AttributeDefinition.ValueType.ENUM, is_filterable=True)
        self.certified = AttributeDefinition.objects.create(code="certified", name_fa="تأیید شده", value_type=AttributeDefinition.ValueType.BOOLEAN, is_filterable=True)
        self.diameter = AttributeDefinition.objects.create(code="diameter", name_fa="قطر", value_type=AttributeDefinition.ValueType.NUMBER, unit="mm", is_filterable=True, is_comparable=True)
        self.internal = AttributeDefinition.objects.create(code="internal", name_fa="داخلی", value_type=AttributeDefinition.ValueType.TEXT, is_filterable=False)
        for attribute in (self.material, self.certified, self.diameter, self.internal):
            CategoryAttribute.objects.create(category=self.category, attribute=attribute, is_filterable=attribute.is_filterable)
        self.first = Product.objects.create(code="TOOL-1", name="Steel tool", slug="tool-1", category=self.category, unit="piece", brand=self.brand)
        self.second = Product.objects.create(code="TOOL-2", name="Plastic tool", slug="tool-2", category=self.category, unit="piece")
        ProductPrice.objects.create(product=self.first, amount="1000", currency="IRR", effective_from=timezone.now())
        ProductPrice.objects.create(product=self.second, amount="2000", currency="IRR", effective_from=timezone.now())
        ProductAttributeValue.objects.create(product=self.first, attribute=self.material, enum_value="steel")
        ProductAttributeValue.objects.create(product=self.first, attribute=self.certified, boolean_value=True)
        ProductAttributeValue.objects.create(product=self.first, attribute=self.diameter, number_value=12)
        ProductAttributeValue.objects.create(product=self.second, attribute=self.material, enum_value="plastic")
        ProductAttributeValue.objects.create(product=self.second, attribute=self.certified, boolean_value=False)
        ProductAttributeValue.objects.create(product=self.second, attribute=self.diameter, number_value=24)

    def query(self, **params):
        response = self.client.get("/api/v1/products/catalog-query/", params)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_brand_enum_boolean_and_numeric_filters(self):
        data = self.query(brand=self.brand.id, attr_material="steel", attr_certified="true", attr_diameter_min="10", attr_diameter_max="20")
        self.assertEqual([item["code"] for item in data["products"]], ["TOOL-1"])
        self.assertEqual(data["applied_filters"]["brand"], [self.brand.id])
        self.assertEqual(data["applied_filters"]["attributes"]["material"], ["steel"])
        self.assertEqual(data["applied_filters"]["attributes"]["diameter"], {"min": "10", "max": "20"})

    def test_price_range_filter_is_exposed_and_applied(self):
        data = self.query(price_min="1500", price_max="2500")
        self.assertEqual([item["code"] for item in data["products"]], ["TOOL-2"])
        price = next(facet for facet in data["facets"] if facet["name"] == "price")
        self.assertEqual(price["unit"], "ریال")
        self.assertEqual(price["selected"], {"min": "1500", "max": "2500"})

    def test_exact_code_outranks_name_match(self):
        exact = Product.objects.create(code="STEEL", name="Generic tool", slug="steel-code", category=self.category, unit="piece")
        Product.objects.create(code="TOOL-STEEL", name="Steel", slug="steel-name", category=self.category, unit="piece")
        data = self.query(q="steel")
        self.assertEqual(data["products"][0]["id"], exact.id)

    def test_manufacturer_part_number_and_alias_are_searchable(self):
        ProductIdentifier.objects.create(product=self.first, identifier_type=ProductIdentifier.Type.MANUFACTURER_PART_NUMBER, display_value="MPN-42")
        ProductIdentifier.objects.create(product=self.second, identifier_type=ProductIdentifier.Type.ALIAS, display_value="legacy tool")
        self.assertEqual(self.query(q="mpn-42")["products"][0]["id"], self.first.id)
        self.assertEqual(self.query(q="legacy tool")["products"][0]["id"], self.second.id)

    def test_persian_arabic_normalization_is_shared(self):
        self.assertEqual(normalize_search_text(" ك‌تاب ۱۲٣ "), " کتاب 123 ".strip())
        ProductIdentifier.objects.create(product=self.first, identifier_type=ProductIdentifier.Type.SKU, display_value="کد-۱۲")
        self.assertEqual(self.query(q="كد-12")["products"][0]["id"], self.first.id)

    def test_search_combines_with_facets_and_supports_zero_results(self):
        filtered = self.query(q="steel", attr_material="steel")
        self.assertEqual([item["id"] for item in filtered["products"]], [self.first.id])
        empty = self.query(q="no-such-industrial-product")
        self.assertEqual(empty["total_count"], 0)
        self.assertEqual(empty["products"], [])

    def test_non_filterable_attribute_is_ignored(self):
        data = self.query(attr_internal="anything")
        self.assertEqual(data["total_count"], 2)
        self.assertNotIn("internal", data["applied_filters"]["attributes"])

    def test_facets_include_counts_and_selected_state(self):
        data = self.query(attr_material="steel")
        material = next(facet for facet in data["facets"] if facet["name"] == "material")
        steel = next(option for option in material["options"] if option["value"] == "steel")
        self.assertEqual(steel["count"], 1)
        self.assertTrue(steel["selected"])

    def test_category_context_limits_visible_facets_to_configured_attributes(self):
        data = self.query(category=self.category.id)
        names = {facet["name"] for facet in data["facets"]}
        self.assertIn("material", names)
        self.assertNotIn("internal", names)

    def test_faceted_query_has_no_per_product_attribute_queries(self):
        with CaptureQueriesContext(connection) as queries:
            data = self.query(q="tool")
        third = Product.objects.create(code="TOOL-3", name="Third tool", slug="tool-3", category=self.category, unit="piece")
        ProductAttributeValue.objects.create(product=third, attribute=self.material, enum_value="steel")
        ProductAttributeValue.objects.create(product=third, attribute=self.certified, boolean_value=True)
        ProductAttributeValue.objects.create(product=third, attribute=self.diameter, number_value=30)
        with CaptureQueriesContext(connection) as larger_queries:
            larger_data = self.query(q="tool")
        self.assertEqual(data["total_count"], 2)
        self.assertEqual(larger_data["total_count"], 3)
        self.assertEqual(len(queries), len(larger_queries))
        self.assertLess(len(queries), 20)
