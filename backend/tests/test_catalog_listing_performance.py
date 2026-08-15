from datetime import timedelta

from django.db import connection
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductImage
from apps.pricing.models import Currency, ProductPrice


class CatalogListingPerformanceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(code="catalog", name_fa="کاتالوگ", slug="catalog")

    def _create_products(self, count):
        now = timezone.now()
        products = []
        start = Product.objects.count()
        for index in range(start, start + count):
            product = Product.objects.create(
                code=f"CAT-{index:03d}", name=f"Catalog {index}", slug=f"catalog-{index}", category=self.category, unit="piece",
            )
            ProductImage.objects.create(product=product, image=f"products/catalog-{index}.jpg", is_primary=index % 2 == 0, sort_order=0)
            ProductImage.objects.create(product=product, image=f"products/catalog-extra-{index}.jpg", is_primary=False, sort_order=1)
            ProductPrice.objects.create(product=product, amount=1000 + index, discount_percentage=10, currency=Currency.IRR, effective_from=now - timedelta(days=1))
            products.append(product)
        return products

    def _list_with_queries(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/v1/products/?page_size=100")
        self.assertEqual(response.status_code, 200)
        return response, len(queries)

    def test_listing_query_budget_does_not_grow_with_products(self):
        self._create_products(4)
        _, small_query_count = self._list_with_queries()
        self._create_products(20)
        response, large_query_count = self._list_with_queries()
        self.assertEqual(small_query_count, large_query_count)
        self.assertLessEqual(large_query_count, 3)
        self.assertEqual(len(response.json()["results"]), 24)

    def test_listing_returns_card_compatible_price_and_single_image(self):
        product = self._create_products(1)[0]
        response, _ = self._list_with_queries()
        item = next(result for result in response.json()["results"] if result["id"] == product.id)
        self.assertEqual(item["category"]["name_fa"], self.category.name_fa)
        self.assertEqual(item["available_quantity"], None)
        self.assertEqual(item["price"]["original_amount"], "1000")
        self.assertEqual(item["price"]["final_amount"], "900.00")
        self.assertEqual(len(item["images"]), 1)
        self.assertIn("image", item["images"][0])

    def test_category_tree_count_excludes_inactive_products(self):
        self._create_products(1)
        Product.objects.create(code="HIDDEN", name="Hidden", slug="hidden", category=self.category, unit="piece", is_active=False)
        response = self.client.get("/api/v1/categories/tree/")
        root = next(item for item in response.json() if item["id"] == self.category.id)
        self.assertEqual(root["product_count"], 1)
