from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductDocument
from apps.content.models import ContentArticle, FAQEntry


class DiscoveryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(code="HVAC", name_fa="تهویه", slug="hvac")
        self.product = Product.objects.create(code="P-1", name="Primary product", slug="primary-product", category=self.category, unit="piece")
        self.other = Product.objects.create(code="P-2", name="Other product", slug="other-product", category=self.category, unit="piece")
        now = timezone.now()
        self.article = ContentArticle.objects.create(content_type="technical_article", slug="primary-article", title_fa="مقاله اصلی", published_at=now, is_published=True)
        self.fallback = ContentArticle.objects.create(content_type="technical_article", slug="category-article", title_fa="مقاله دسته", published_at=now, is_published=True)
        self.future = ContentArticle.objects.create(content_type="news", slug="future-article", title_fa="آینده", published_at=now + timedelta(days=1), is_published=True)
        self.article.products.add(self.product)
        self.fallback.catalog_categories.add(self.category)
        self.faq = FAQEntry.objects.create(slug="product-faq", question_fa="پرسش", answer_fa="پاسخ", is_published=True)
        self.faq.products.add(self.product)
        self.document = ProductDocument.objects.create(product=self.product, document_type="datasheet", title_fa="دیتاشیت", file=SimpleUploadedFile("sheet.pdf", b"pdf", content_type="application/pdf"), is_published=True)

    def test_product_discovery_prioritizes_direct_and_excludes_private_future_records(self):
        response = self.client.get("/api/v1/catalog/products/primary-product/discovery/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([item["slug"] for item in data["articles"]], ["primary-article", "category-article"])
        self.assertEqual([item["slug"] for item in data["faqs"]], ["product-faq"])
        self.assertEqual([item["id"] for item in data["resources"]], [self.document.id])
        self.assertNotIn("future-article", [item["slug"] for item in data["articles"]])

    def test_article_discovery_excludes_current_and_deduplicates_shared_context(self):
        related = ContentArticle.objects.create(content_type="news", slug="related", title_fa="مرتبط", published_at=timezone.now(), is_published=True)
        related.products.add(self.product)
        related.catalog_categories.add(self.category)
        response = self.client.get("/api/v1/content/articles/primary-article/discovery/")
        self.assertEqual(response.status_code, 200)
        slugs = [item["slug"] for item in response.json()["articles"]]
        self.assertEqual(slugs.count("related"), 1)
        self.assertNotIn("primary-article", slugs)

    def test_discovery_limit_and_private_resource_safety(self):
        for index in range(8):
            ContentArticle.objects.create(content_type="news", slug=f"extra-{index}", title_fa=f"اضافی {index}", published_at=timezone.now(), is_published=True).catalog_categories.add(self.category)
        ProductDocument.objects.create(product=self.product, document_type="manual", title_fa="Internal", file=SimpleUploadedFile("internal.pdf", b"pdf", content_type="application/pdf"), is_published=False)
        data = self.client.get("/api/v1/catalog/products/primary-product/discovery/").json()
        self.assertLessEqual(len(data["articles"]), 4)
        self.assertLessEqual(len(data["resources"]), 5)
        self.assertEqual(len(data["resources"]), 1)
