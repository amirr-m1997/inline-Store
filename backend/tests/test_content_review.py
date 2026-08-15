from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.company.models import CompanyCertification, CompanyLocation, CompanySection
from apps.company.review import review_record


class ContentReviewTests(TestCase):
    def test_review_classifies_verification_and_translation_gaps(self):
        location = CompanyLocation.objects.create(location_type="factory", name_fa="کارخانه", source_url="https://mehrasl.ir/farsi/about-us/")
        certification = CompanyCertification.objects.create(title_fa="ISO", certificate_code="ISO 9000", verification_status="unverified", is_published=False)

        location_review = review_record("CompanyLocation", location)
        certification_review = review_record("CompanyCertification", certification)

        self.assertEqual(location_review["classification"], "B")
        self.assertIn("English translation", location_review["missing"])
        self.assertEqual(certification_review["classification"], "B")
        self.assertIn("issuer", certification_review["missing"])

    def test_review_report_is_read_only_and_lists_source_fields(self):
        section = CompanySection.objects.create(section_type="introduction", title_fa="معرفی", source_url="https://mehrasl.ir/farsi/about-us/", is_published=False)
        output = StringIO()
        call_command("content_review_report", stdout=output)
        text = output.getvalue()

        self.assertIn("CompanySection", text)
        self.assertIn("https://mehrasl.ir/farsi/about-us/", text)
        self.assertEqual(CompanySection.objects.get(pk=section.pk).is_published, False)

    def test_csv_export_contains_approval_columns_and_is_read_only(self):
        section = CompanySection.objects.create(section_type="introduction", title_fa="معرفی", is_published=False)
        output = StringIO()
        call_command("export_content_approval", stdout=output)
        header = output.getvalue().splitlines()[0]
        for column in ("content_type", "record_id", "verification_required", "recommended_decision", "business_decision", "business_notes"):
            self.assertIn(column, header)
        self.assertFalse(CompanySection.objects.get(pk=section.pk).is_published)
