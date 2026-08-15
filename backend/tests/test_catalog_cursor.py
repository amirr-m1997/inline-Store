from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import Category, Product


class CatalogCursorPaginationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="cursor", name_fa="کاتالوگ", slug="cursor")
        for index in range(5):
            Product.objects.create(code=f"CUR-{index:02d}", name=f"Industrial item {index}", slug=f"cursor-{index}", category=self.category, unit="piece")

    def request(self, **params):
        response = self.client.get("/api/v1/products/catalog-query/", params)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_first_and_next_cursor_pages_have_no_duplicates(self):
        first = self.request(page_size=2)
        second = self.request(page_size=2, cursor=first["next_cursor"])
        first_codes = [item["code"] for item in first["products"]]
        second_codes = [item["code"] for item in second["products"]]
        self.assertEqual(first_codes, ["CUR-00", "CUR-01"])
        self.assertEqual(second_codes, ["CUR-02", "CUR-03"])
        self.assertFalse(set(first_codes) & set(second_codes))
        self.assertTrue(second["has_more"])

    def test_end_of_results_and_deterministic_tie_breaker(self):
        page = self.request(page_size=10, ordering="name")
        self.assertEqual([item["code"] for item in page["products"]], [f"CUR-{index:02d}" for index in range(5)])
        self.assertFalse(page["has_more"])
        self.assertIsNone(page["next_cursor"])

    def test_search_and_sort_cursor_modes(self):
        first = self.request(q="industrial", page_size=1, sort="relevance")
        second = self.request(q="industrial", page_size=1, sort="relevance", cursor=first["next_cursor"])
        self.assertEqual(first["products"][0]["code"], "CUR-00")
        self.assertEqual(second["products"][0]["code"], "CUR-01")

    def test_filters_and_cursor_are_bound_to_query_context(self):
        first = self.request(category=self.category.id, page_size=2)
        mismatch = self.client.get("/api/v1/products/catalog-query/", {"cursor": first["next_cursor"], "page_size": 2, "q": "different"})
        self.assertEqual(mismatch.status_code, 400)

    def test_malformed_cursor_is_rejected(self):
        response = self.client.get("/api/v1/products/catalog-query/", {"cursor": "not-a-signed-cursor", "page_size": 2})
        self.assertEqual(response.status_code, 400)

    def test_cursor_query_count_is_constant_across_result_sizes(self):
        with CaptureQueriesContext(connection) as first_queries:
            first = self.request(page_size=2)
        with CaptureQueriesContext(connection) as second_queries:
            self.request(page_size=2, cursor=first["next_cursor"])
        self.assertEqual(len(first_queries), len(second_queries))
