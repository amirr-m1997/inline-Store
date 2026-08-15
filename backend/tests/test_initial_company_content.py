from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.company.models import Capability, CompanyCertification, CompanyLocation, CompanyMilestone, CompanySection, Industry


class InitialCompanyContentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command("import_mehrasl_content", stdout=StringIO())

    def test_population_is_idempotent_and_publishes_only_low_risk_content(self):
        output = StringIO()
        call_command("populate_initial_company_content", stdout=output)
        counts = (CompanySection.objects.count(), CompanyLocation.objects.count(), CompanyMilestone.objects.count(), Industry.objects.count(), Capability.objects.count())
        call_command("populate_initial_company_content", stdout=StringIO())
        self.assertEqual(counts, (CompanySection.objects.count(), CompanyLocation.objects.count(), CompanyMilestone.objects.count(), Industry.objects.count(), Capability.objects.count()))
        self.assertEqual(CompanySection.objects.filter(is_published=True).count(), 4)
        self.assertEqual(CompanyLocation.objects.filter(is_published=True).count(), 6)
        self.assertFalse(CompanyLocation.objects.get(name_fa="کارخانجات برودتی آریا").is_published)
        self.assertEqual(CompanyMilestone.objects.filter(is_published=True).count(), 1)
        self.assertEqual(Industry.objects.filter(is_published=True).count(), 7)
        self.assertEqual(Capability.objects.filter(is_published=True).count(), 3)
        section = CompanySection.objects.filter(migration_notes__contains="initial-content:mehrasl-9.9").first()
        section.is_published = False
        section.save(update_fields=("is_published",))
        call_command("populate_initial_company_content", stdout=StringIO())
        self.assertFalse(CompanySection.objects.get(pk=section.pk).is_published)

    def test_certifications_remain_unpublished_and_verification_gated(self):
        call_command("populate_initial_company_content", stdout=StringIO())
        self.assertFalse(CompanyCertification.objects.filter(is_published=True).exists())
        self.assertTrue(CompanyCertification.objects.filter(verification_status="unverified").exists())

    def test_provenance_and_public_apis_expose_populated_content(self):
        call_command("populate_initial_company_content", stdout=StringIO())
        self.assertTrue(CompanySection.objects.filter(migration_notes__contains="initial-content:mehrasl-9.9").exists())
        self.assertEqual(Industry.objects.filter(is_published=True, source_url__startswith="https://mehrasl.ir/").count(), 7)
        self.assertEqual(Capability.objects.filter(is_published=True, source_url__startswith="https://mehrasl.ir/").count(), 3)

        self.assertEqual(len(self.client.get("/api/v1/company/sections/").json()), 4)
        self.assertEqual(len(self.client.get("/api/v1/company/locations/").json()), 6)
        self.assertEqual(len(self.client.get("/api/v1/company/milestones/").json()), 1)
        self.assertEqual(len(self.client.get("/api/v1/company/industries/").json()), 7)
        self.assertEqual(len(self.client.get("/api/v1/company/capabilities/").json()), 3)

    def test_existing_manual_content_is_not_overwritten(self):
        item = CompanySection.objects.create(section_type="introduction", title_fa="Custom section", body_fa="Owner wording", is_published=False, migration_notes="manual edit")
        call_command("populate_initial_company_content", stdout=StringIO())
        item.refresh_from_db()
        self.assertEqual(item.body_fa, "Owner wording")
        self.assertFalse(item.is_published)
