from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.company.models import Capability, CompanyCertification, CompanyHonor, CompanyLocation, CompanyMilestone, Industry


class OfficialCompanyContentTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unpublished_and_unverified_content_is_not_public(self):
        location = CompanyLocation.objects.create(location_type="factory", name_fa="Draft factory", is_published=False)
        milestone = CompanyMilestone.objects.create(title_fa="Draft milestone", is_published=False)
        certification = CompanyCertification.objects.create(title_fa="ISO", verification_status="unverified", is_published=True)
        honor = CompanyHonor.objects.create(title_fa="Honor", verification_required=True, is_published=True)
        industry = Industry.objects.create(slug="draft-industry", name_fa="Draft industry", is_published=False)
        capability = Capability.objects.create(slug="draft-capability", title_fa="Draft capability", is_published=False)

        self.assertEqual(self.client.get("/api/v1/company/locations/").json(), [])
        self.assertEqual(self.client.get("/api/v1/company/milestones/").json(), [])
        self.assertEqual(self.client.get("/api/v1/company/certifications/").json(), [])
        self.assertEqual(self.client.get("/api/v1/company/honors/").json(), [])
        self.assertEqual(self.client.get("/api/v1/company/industries/").json(), [])
        self.assertEqual(self.client.get("/api/v1/company/capabilities/").json(), [])
        self.assertTrue(location and milestone and certification and honor and industry and capability)

    def test_published_location_and_verified_certification_serialize(self):
        location = CompanyLocation.objects.create(location_type="office", name_fa="Sales office", address_fa="Tehran", is_published=True)
        certification = CompanyCertification.objects.create(title_fa="Verified standard", verification_status="verified", is_published=True)
        industry = Industry.objects.create(slug="approved-industry", name_fa="Approved industry", is_active=True, is_published=True)
        capability = Capability.objects.create(slug="approved-capability", title_fa="Approved capability", summary_fa="Summary", body_fa="Body", is_active=True, is_published=True)

        locations = self.client.get("/api/v1/company/locations/").json()
        certifications = self.client.get("/api/v1/company/certifications/").json()

        self.assertEqual(locations[0]["id"], location.id)
        self.assertEqual(locations[0]["address_fa"], "Tehran")
        self.assertEqual(certifications[0]["id"], certification.id)
        self.assertEqual(self.client.get("/api/v1/company/industries/").json()[0]["id"], industry.id)
        self.assertEqual(self.client.get("/api/v1/company/capabilities/").json()[0]["id"], capability.id)

    def test_import_command_is_idempotent_and_keeps_records_draft(self):
        first = StringIO()
        call_command("import_mehrasl_content", stdout=first)
        first_counts = (CompanyLocation.objects.count(), CompanyMilestone.objects.count(), CompanyCertification.objects.count(), Industry.objects.count())
        second = StringIO()
        call_command("import_mehrasl_content", stdout=second)
        second_counts = (CompanyLocation.objects.count(), CompanyMilestone.objects.count(), CompanyCertification.objects.count(), Industry.objects.count())

        self.assertEqual(first_counts, second_counts)
        self.assertFalse(CompanyLocation.objects.filter(is_published=True).exists())
        self.assertFalse(CompanyMilestone.objects.filter(is_published=True).exists())
        self.assertFalse(CompanyCertification.objects.filter(is_published=True).exists())
        self.assertFalse(Industry.objects.filter(is_published=True).exists())
