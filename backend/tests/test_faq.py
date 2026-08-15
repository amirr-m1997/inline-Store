from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.company.models import Capability, Industry
from apps.content.models import ContentArticle, FAQEntry


class FAQApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(code="HVAC", name_fa="تهویه", name_en="HVAC", slug="hvac")
        self.product = Product.objects.create(code="P-001", name="Demo product", slug="demo-product", category=self.category, unit="عدد")
        self.industry = Industry.objects.create(slug="industry", name_fa="صنعت", name_en="Industry", is_active=True, is_published=True)
        self.capability = Capability.objects.create(slug="capability", title_fa="توانمندی", title_en="Capability", is_active=True, is_published=True)
        self.article = ContentArticle.objects.create(content_type="technical_article", slug="supporting-article", title_fa="مقاله پشتیبان", is_active=True, is_published=True, published_at=timezone.now())
        self.faq = FAQEntry.objects.create(slug="published-faq", faq_type="technical", question_fa="پرسش فنی", question_en="Technical question", answer_fa="پاسخ فنی", answer_en="Technical answer", is_active=True, is_published=True)
        self.faq.products.add(self.product)
        self.faq.categories.add(self.category)
        self.faq.industries.add(self.industry)
        self.faq.capabilities.add(self.capability)
        self.faq.articles.add(self.article)
        FAQEntry.objects.create(slug="draft-faq", faq_type="support", question_fa="پیش‌نویس", answer_fa="پاسخ", is_published=False)
        FAQEntry.objects.create(slug="inactive-faq", faq_type="support", question_fa="غیرفعال", answer_fa="پاسخ", is_active=False, is_published=True)

    def test_public_listing_and_detail_hide_private_records(self):
        response = self.client.get("/api/v1/content/faqs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["slug"] for item in response.json()], ["published-faq"])
        detail = self.client.get("/api/v1/content/faqs/published-faq/?lang=en").json()
        self.assertEqual(detail["question"], "Technical question")
        self.assertEqual(detail["answer"], "Technical answer")
        self.assertEqual(detail["related_products"][0]["slug"], "demo-product")
        self.assertEqual(detail["related_categories"][0]["slug"], "hvac")
        self.assertEqual(detail["related_industries"][0]["slug"], "industry")
        self.assertEqual(detail["related_capabilities"][0]["slug"], "capability")
        self.assertEqual(detail["related_articles"][0]["slug"], "supporting-article")
        self.assertEqual(self.client.get("/api/v1/content/faqs/draft-faq/").status_code, 404)

    def test_explicit_relationship_and_type_filters(self):
        for parameter, value in (("type", "technical"), ("product", "demo-product"), ("category", "hvac"), ("industry", "industry"), ("capability", "capability"), ("article", "supporting-article")):
            response = self.client.get(f"/api/v1/content/faqs/?{parameter}={value}")
            self.assertEqual(response.status_code, 200, parameter)
            self.assertEqual([item["slug"] for item in response.json()], ["published-faq"], parameter)

    def test_public_faq_queryset_is_bounded_and_prefetched(self):
        with self.assertNumQueries(6):
            response = self.client.get("/api/v1/content/faqs/published-faq/")
        self.assertEqual(response.status_code, 200)


class FAQAdminAndDemoTests(TestCase):
    def test_admin_changelist_is_available(self):
        user = get_user_model().objects.create_superuser(username="admin", email="admin@example.com", password="test-password")
        client = APIClient()
        client.login(username=user.username, password="test-password")
        self.assertEqual(client.get("/admin/content/faqentry/").status_code, 200)

    @override_settings(DEBUG=True)
    def test_demo_faq_seed_is_idempotent_and_cleanup_safe(self):
        manual = FAQEntry.objects.create(slug="manual-faq", question_fa="Manual", answer_fa="Manual answer")
        call_command("populate_demo_content", stdout=StringIO())
        first = FAQEntry.objects.filter(migration_notes__contains="demo-content:phase-11.1").count()
        call_command("populate_demo_content", stdout=StringIO())
        self.assertEqual(first, FAQEntry.objects.filter(migration_notes__contains="demo-content:phase-11.1").count())
        call_command("remove_demo_content", stdout=StringIO())
        self.assertTrue(FAQEntry.objects.filter(pk=manual.pk).exists())
        self.assertFalse(FAQEntry.objects.filter(migration_notes__contains="demo-content:phase-11.1").exists())
