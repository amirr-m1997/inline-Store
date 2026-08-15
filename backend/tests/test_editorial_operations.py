from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.content.models import ContentArticle, FAQEntry
from apps.content.review import duplicate_groups, evaluate_record


class EditorialOperationsTests(TestCase):
    def test_review_state_is_independent_from_publication_state(self):
        article = ContentArticle.objects.create(content_type="news", slug="ready-private", title_fa="خبر آماده بررسی", review_status="ready", is_published=False)
        self.assertEqual(article.review_status, "ready")
        self.assertFalse(article.is_published)
        self.assertNotIn("published", dict(ContentArticle.ReviewStatus.choices))

    def test_quality_flags_and_ready_state_do_not_publish(self):
        article = ContentArticle.objects.create(content_type="product_guide", slug="quality", title_fa="کوتاه", review_status="ready", is_published=False)
        review = evaluate_record(article)
        self.assertIn("title_en", review["missing"])
        self.assertIn("seo_title_fa", review["missing"])
        self.assertIn("product_guide_without_product_or_category", review["warnings"])
        self.assertFalse(article.is_published)

    def test_duplicate_signals_are_reported_without_deleting_records(self):
        first = ContentArticle.objects.create(content_type="news", slug="same", title_fa="عنوان تکراری", source_url="https://mehrasl.ir/farsi/news/one/")
        second = ContentArticle.objects.create(content_type="news", slug="same-copy", title_fa="عنوان تکراری", source_url="https://mehrasl.ir/farsi/news/two/")
        groups = duplicate_groups([first, second])
        self.assertTrue(any(key[0] == "title" for key in groups))
        self.assertEqual(ContentArticle.objects.count(), 2)

    def test_review_command_is_read_only_and_reports_both_models(self):
        ContentArticle.objects.create(content_type="news", slug="review", title_fa="خبر", is_published=False)
        FAQEntry.objects.create(slug="review-faq", question_fa="پرسش", answer_fa="پاسخ", is_published=False)
        before = (ContentArticle.objects.count(), FAQEntry.objects.count())
        output = StringIO()
        call_command("content_editorial_review", stdout=output)
        self.assertIn("total articles: 1", output.getvalue())
        self.assertIn("total FAQs: 1", output.getvalue())
        self.assertEqual(before, (ContentArticle.objects.count(), FAQEntry.objects.count()))

    def test_csv_export_has_review_columns_and_is_read_only(self):
        ContentArticle.objects.create(content_type="news", slug="csv", title_fa="خبر", is_published=False)
        output = StringIO()
        call_command("export_editorial_review", stdout=output)
        header = output.getvalue().splitlines()[0]
        self.assertIn("missing_fields", header)
        self.assertIn("recommended_action", header)
        for column in ("provenance_type", "related_brands", "duplicate_candidates", "published_at"):
            self.assertIn(column, header)
        self.assertEqual(ContentArticle.objects.count(), 1)

    def test_csv_export_keeps_persian_utf8_content(self):
        ContentArticle.objects.create(content_type="news", slug="persian-csv", title_fa="خبر فارسی برای بررسی", is_published=False)
        output = StringIO()
        call_command("export_editorial_review", stdout=output)
        self.assertIn("خبر فارسی برای بررسی", output.getvalue())


@override_settings(DEBUG=True)
class OfficialEditorialImportTests(TestCase):
    def test_import_is_idempotent_and_preserves_manual_edits(self):
        first_output = StringIO()
        call_command("import_mehrasl_editorial_content", stdout=first_output)
        self.assertEqual(ContentArticle.objects.filter(source_fingerprint__gt="").count(), 3)
        self.assertEqual(ContentArticle.objects.filter(is_published=True).count(), 0)
        self.assertEqual(ContentArticle.objects.filter(review_status="needs_review").count(), 3)
        first = ContentArticle.objects.order_by("id").first()
        first.body_fa = "Manual editorial edit"
        first.save(update_fields=("body_fa",))
        second_output = StringIO()
        call_command("import_mehrasl_editorial_content", stdout=second_output)
        self.assertEqual(ContentArticle.objects.count(), 3)
        self.assertEqual(ContentArticle.objects.get(pk=first.pk).body_fa, "Manual editorial edit")
        self.assertIn("preserved_existing=1", second_output.getvalue())
