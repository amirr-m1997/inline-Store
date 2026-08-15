from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductBrand, ProductIdentifier
from apps.catalog.services import CatalogQueryService
from apps.content.models import ContentArticle


class UnifiedSearchApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(code="HVAC", name_fa="تأسیسات", name_en="HVAC", slug="hvac")
        self.brand = ProductBrand.objects.create(name="ChillerCo", code="CHILL", slug="chillerco", is_active=True, is_published=True)
        self.product = Product.objects.create(code="P-CH-001", name="Industrial Chiller", slug="industrial-chiller", category=self.category, unit="piece", brand=self.brand, is_active=True)
        self.screw_product = Product.objects.create(code="P-SCR-001", name="پیچ صنعتی نمونه", slug="industrial-screw", category=self.category, unit="piece", is_active=True)
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.SKU, display_value="SKU-CH-001")
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.MANUFACTURER_PART_NUMBER, display_value="MPN-CH-42")
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.ALIAS, display_value="cooling unit")
        ProductIdentifier.objects.create(product=self.product, identifier_type=ProductIdentifier.Type.ALIAS, display_value="کد-چ")
        self.article = ContentArticle.objects.create(content_type="technical_article", slug="chiller-guide", title_fa="راهنمای چیلر", title_en="Chiller guide", excerpt_fa="انتخاب چیلر صنعتی", body_fa="ظرفیت و راندمان چیلر", is_active=True, is_published=True, published_at=timezone.now())
        ContentArticle.objects.create(content_type="news", slug="draft-chiller", title_fa="چیلر پیش‌نویس", is_published=False)
        ContentArticle.objects.create(content_type="news", slug="future-chiller", title_fa="چیلر آینده", is_published=True, published_at=timezone.now() + timedelta(days=1))
        Product.objects.create(code="P-INACTIVE", name="Industrial Chiller", slug="inactive-chiller", category=self.category, unit="piece", is_active=False)

    def search(self, query, **params):
        response = self.client.get("/api/v1/search/", {"q": query, **params})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_product_title_identifier_and_alias_search_are_deduplicated(self):
        for query in ("Chiller", "SKU-CH-001", "MPN-CH-42", "cooling unit"):
            data = self.search(query)
            self.assertEqual([item["id"] for item in data["products"]], [self.product.id], query)

    def test_category_brand_and_editorial_groups(self):
        self.assertEqual(self.search("HVAC")["categories"][0]["slug"], "hvac")
        self.assertEqual(self.search("ChillerCo")["brands"][0]["slug"], "chillerco")
        self.assertEqual(self.search("capacity")["articles"], [])
        self.assertEqual(self.search("راندمان")["articles"][0]["slug"], "chiller-guide")
        self.assertEqual(self.search("Chiller")["articles"][0]["slug"], "chiller-guide")

    def test_public_exclusions_normalization_limits_and_empty_query(self):
        self.assertEqual(self.search("كد-چ")["products"][0]["id"], self.product.id)
        self.assertNotIn("draft-chiller", [item["slug"] for item in self.search("پیش‌نویس چیلر")["articles"]])
        self.assertNotIn("future-chiller", [item["slug"] for item in self.search("چیلر آینده")["articles"]])
        self.assertEqual(self.search(" ")["counts"], {"products": 0, "categories": 0, "brands": 0, "articles": 0, "faqs": 0})
        self.assertEqual(self.client.get("/api/v1/search/", {"q": "x"}).status_code, 200)
        self.assertEqual(self.client.get("/api/v1/search/", {"q": "x" * 121}).status_code, 400)

    def test_each_group_is_bounded(self):
        for index in range(12):
            Product.objects.create(code=f"CH-{index}", name=f"Chiller {index}", slug=f"chiller-{index}", category=self.category, unit="piece")
        data = self.search("Chiller")
        self.assertLessEqual(len(data["products"]), 8)

    def test_unified_products_match_catalog_service_for_persian_query(self):
        catalog_ids = list(CatalogQueryService(Product.objects.filter(is_active=True), {"q": "پیچ"}).apply().values_list("id", flat=True))
        unified_ids = [item["id"] for item in self.search("پیچ")["products"]]
        self.assertEqual(unified_ids, catalog_ids[:8])
