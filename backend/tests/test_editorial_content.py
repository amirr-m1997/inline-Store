from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductBrand
from apps.company.models import Capability, Industry
from apps.content.models import ContentArticle, ContentCategory


class EditorialContentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.catalog_category = Category.objects.create(code="HVAC", name_fa="تهویه", slug="hvac")
        self.product = Product.objects.create(code="P-001", name="Demo product", slug="demo-product", category=self.catalog_category, unit="عدد")
        self.brand = ProductBrand.objects.create(name="Brand", code="BR", slug="brand", is_active=True, is_published=True)
        self.industry = Industry.objects.create(slug="industry", name_fa="صنعت", is_active=True, is_published=True)
        self.capability = Capability.objects.create(slug="capability", title_fa="توانمندی", is_active=True, is_published=True)
        self.category = ContentCategory.objects.create(slug="technical", name_fa="فنی", is_active=True, is_published=True)
        self.published = ContentArticle.objects.create(
            content_type=ContentArticle.ContentType.TECHNICAL_ARTICLE, slug="published-article", title_fa="مقاله منتشرشده",
            title_en="Published article", excerpt_fa="خلاصه", body_fa="متن کامل", seo_title_fa="SEO title",
            seo_description_fa="SEO description", category=self.category, published_at=timezone.now(), is_active=True, is_published=True,
        )
        self.published.products.add(self.product)
        self.published.catalog_categories.add(self.catalog_category)
        self.published.brands.add(self.brand)
        self.published.industries.add(self.industry)
        self.published.capabilities.add(self.capability)
        ContentArticle.objects.create(content_type="news", slug="draft", title_fa="پیش‌نویس", is_published=False)
        ContentArticle.objects.create(content_type="news", slug="future", title_fa="آینده", is_published=True, published_at=timezone.now() + timedelta(days=1))
        ContentArticle.objects.create(content_type="news", slug="inactive", title_fa="غیرفعال", is_active=False, is_published=True, published_at=timezone.now())

    def test_public_listing_excludes_draft_future_and_inactive(self):
        response = self.client.get("/api/v1/content/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["slug"] for item in response.json()["results"]], ["published-article"])

    def test_detail_contains_full_localized_seo_and_relationships(self):
        response = self.client.get("/api/v1/content/articles/published-article/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["body"], "متن کامل")
        self.assertEqual(data["seo_title"], "SEO title")
        self.assertEqual(data["related_products"][0]["slug"], "demo-product")
        self.assertEqual(data["related_catalog_categories"][0]["slug"], "hvac")
        self.assertEqual(data["related_brands"][0]["slug"], "brand")
        self.assertEqual(data["related_industries"][0]["slug"], "industry")
        self.assertEqual(data["related_capabilities"][0]["slug"], "capability")

    def test_content_type_category_and_commerce_filters(self):
        for parameter, value in (
            ("content_type", "technical_article"), ("category", "technical"), ("product", "demo-product"),
            ("catalog_category", "hvac"), ("brand", "brand"), ("industry", "industry"), ("capability", "capability"), ("featured", "true"),
        ):
            self.published.is_featured = True
            self.published.save(update_fields=("is_featured",))
            response = self.client.get(f"/api/v1/content/articles/?{parameter}={value}")
            self.assertEqual(response.status_code, 200, parameter)
            self.assertEqual([item["slug"] for item in response.json()["results"]], ["published-article"], parameter)

    def test_category_endpoint_exposes_only_public_categories(self):
        ContentCategory.objects.create(slug="draft-topic", name_fa="پیش‌نویس", is_published=False)
        response = self.client.get("/api/v1/content/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["slug"] for item in response.json()], ["technical"])

    def test_article_relationships_are_prefetched(self):
        with self.assertNumQueries(6):
            response = self.client.get("/api/v1/content/articles/published-article/")
        self.assertEqual(response.status_code, 200)


@override_settings(DEBUG=True)
class EditorialDemoLifecycleTests(TestCase):
    def test_seed_is_idempotent_and_cleanup_preserves_manual_editorial_records(self):
        manual_category = ContentCategory.objects.create(slug="manual", name_fa="Manual", is_active=True, is_published=False)
        manual_article = ContentArticle.objects.create(content_type="news", slug="manual", title_fa="Manual", category=manual_category)
        call_command("populate_demo_content", stdout=StringIO())
        first = (ContentCategory.objects.filter(migration_notes__contains="demo-content:phase-11.1").count(), ContentArticle.objects.filter(migration_notes__contains="demo-content:phase-11.1").count())
        call_command("populate_demo_content", stdout=StringIO())
        second = (ContentCategory.objects.filter(migration_notes__contains="demo-content:phase-11.1").count(), ContentArticle.objects.filter(migration_notes__contains="demo-content:phase-11.1").count())
        self.assertEqual(first, (3, 7))
        self.assertEqual(first, second)
        call_command("remove_demo_content", stdout=StringIO())
        self.assertTrue(ContentArticle.objects.filter(pk=manual_article.pk).exists())
        self.assertTrue(ContentCategory.objects.filter(pk=manual_category.pk).exists())
        self.assertFalse(ContentArticle.objects.filter(migration_notes__contains="demo-content:phase-11.1").exists())


class EditorialAdminTests(TestCase):
    def test_admin_changelist_is_available(self):
        User = get_user_model()
        user = User.objects.create_superuser(username="admin", email="admin@example.com", password="test-password")
        client = APIClient()
        client.login(username=user.username, password="test-password")
        response = client.get("/admin/content/contentarticle/")
        self.assertEqual(response.status_code, 200)
