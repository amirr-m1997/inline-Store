from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductBrand
from apps.company.models import Capability, CompanySection


class CompanyContentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(code="cables", name_fa="کابل", slug="cables")
        self.product = Product.objects.create(code="CB-1", name="Cable", slug="cable", category=self.category, unit="piece")

    def test_company_sections_expose_only_active_published_content(self):
        CompanySection.objects.create(section_type="value", title_fa="Draft", is_published=False)
        CompanySection.objects.create(section_type="value", title_fa="Visible", is_published=True)

        response = self.client.get("/api/v1/company/sections/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title_fa"] for item in response.json()], ["Visible"])

    def test_capability_detail_and_list_exclude_unpublished_items(self):
        Capability.objects.create(slug="draft", title_fa="Draft")
        visible = Capability.objects.create(slug="cutting", title_fa="Cutting", is_published=True)
        visible.categories.add(self.category)
        visible.products.add(self.product)

        listing = self.client.get("/api/v1/company/capabilities/")
        detail = self.client.get("/api/v1/company/capabilities/cutting/")
        hidden = self.client.get("/api/v1/company/capabilities/draft/")

        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["slug"] for item in listing.json()], ["cutting"])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["categories"][0]["slug"], "cables")
        self.assertEqual(detail.json()["products"][0]["slug"], "cable")
        self.assertEqual(hidden.status_code, 404)

    def test_brand_directory_uses_only_published_brands_with_slugs(self):
        ProductBrand.objects.create(name="Legacy", code="LEGACY")
        visible = ProductBrand.objects.create(name="Acme", code="ACME", slug="acme", is_published=True)
        self.product.brand = visible
        self.product.save(update_fields=["brand"])

        listing = self.client.get("/api/v1/brands/")
        detail = self.client.get("/api/v1/brands/acme/")

        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["slug"] for item in listing.json()], ["acme"])
        self.assertEqual(listing.json()[0]["product_count"], 1)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["products"][0]["slug"], "cable")
