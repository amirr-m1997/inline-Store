from datetime import date, datetime

from django.test import SimpleTestCase

from apps.common.jalali import format_document_date, format_jalali, gregorian_to_jalali


class JalaliPresentationTests(SimpleTestCase):
    def test_known_nowruz_boundaries(self):
        self.assertEqual(gregorian_to_jalali(2024, 3, 20), (1403, 1, 1))
        self.assertEqual(format_jalali(date(2024, 3, 20)), "۱۴۰۳/۰۱/۰۱")

    def test_datetime_has_optional_time(self):
        value = datetime(2024, 3, 20, 9, 5)
        self.assertEqual(format_jalali(value, with_time=True), "۱۴۰۳/۰۱/۰۱ ۰۹:۰۵")

    def test_english_document_date_remains_gregorian(self):
        value = datetime(2024, 3, 20, 9, 5)
        self.assertEqual(format_document_date(value, locale="en", with_time=True), "2024-03-20 09:05")
