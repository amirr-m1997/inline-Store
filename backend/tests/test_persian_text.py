"""Arabic keyboard variants must never reach the browser (Persian display)."""

from django.test import TestCase

from apps.catalog.models import Category, Product
from apps.common.textnorm import normalize_json_data, normalize_persian_text

# Explicit escapes: the source file itself must stay free of Arabic variants.
AR_YEH = "\u064a"  # ي
AR_KAF = "\u0643"  # ك
AR_ALEF_MAKSURA = "\u0649"  # ى
AR_TEH_MARBUTA = "\u0629"  # ة
FA_YEH = "\u06cc"  # ی
FA_KAF = "\u06a9"  # ک
FA_HEH = "\u0647"  # ه


class NormalizePersianTextTests(TestCase):
    def test_arabic_letters_map_to_persian(self):
        self.assertEqual(normalize_persian_text(AR_YEH + AR_KAF), FA_YEH + FA_KAF)
        self.assertEqual(normalize_persian_text(AR_ALEF_MAKSURA), FA_YEH)
        self.assertEqual(normalize_persian_text(AR_TEH_MARBUTA), FA_HEH)

    def test_arabic_indic_digits_map_to_persian_digits(self):
        self.assertEqual(normalize_persian_text("\u0660\u0661\u0662"), "\u06f0\u06f1\u06f2")

    def test_correct_persian_text_is_untouched(self):
        # ئ, ؤ, أ and إ are correct Persian orthography (جزئیات، مؤسسه، تأمین)
        # and share code points with Arabic keyboards, so they must NOT be
        # rewritten — verified: every أ in production data is the word تأمین.
        text = "جزئیات مؤسسه رئیس تأمین تأیید ۱۲۳ ABC-456"
        self.assertEqual(normalize_persian_text(text), text)

    def test_non_strings_pass_through(self):
        self.assertIsNone(normalize_persian_text(None))
        self.assertEqual(normalize_persian_text(42), 42)

    def test_nested_json_structures_are_normalized(self):
        data = {"a": [AR_YEH, {"b": AR_KAF, "c": 1}],}
        self.assertEqual(
            normalize_json_data(data), {"a": [FA_YEH, {"b": FA_KAF, "c": 1}]}
        )


class PersianDisplayMiddlewareTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            code="ar-test", name_fa="دسته" + AR_YEH, slug="ar-test"
        )

    def test_product_api_returns_persian_forms(self):
        Product.objects.create(
            code="AR-001",
            name="کمپرسور" + AR_YEH,
            slug="ar-001",
            category=self.category,
            unit="piece",
            description="<p>ظرفیت سرمایش" + AR_KAF + "</p>",
        )
        response = self.client.get("/api/v1/products/?search=AR-001")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn(FA_YEH, body)
        self.assertIn(FA_KAF, body)
        self.assertNotIn(AR_YEH, body)
        self.assertNotIn(AR_KAF, body)

    def test_non_json_responses_pass_through(self):
        Product.objects.create(
            code="AR-002", name="x", slug="ar-002", category=self.category, unit="piece"
        )
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
