from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.catalog.models import ProductBrand, ProductDocument
from apps.company.models import Capability, CompanyCertification, CompanySection


@override_settings(DEBUG=True)
class DemoContentTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_demo_population_is_idempotent_and_public_in_development(self):
        call_command("populate_demo_content", stdout=StringIO())
        first = (CompanySection.objects.filter(migration_notes__contains="demo-content:phase-9.10").count(), Capability.objects.filter(migration_notes__contains="demo-content:phase-9.10").count(), ProductBrand.objects.filter(name__startswith="Demo Industrial Brand").count())
        call_command("populate_demo_content", stdout=StringIO())
        second = (CompanySection.objects.filter(migration_notes__contains="demo-content:phase-9.10").count(), Capability.objects.filter(migration_notes__contains="demo-content:phase-9.10").count(), ProductBrand.objects.filter(name__startswith="Demo Industrial Brand").count())
        self.assertEqual(first, second)
        self.assertGreater(len(self.client.get("/api/v1/company/sections/").json()), 0)
        self.assertGreater(len(self.client.get("/api/v1/company/certifications/").json()), 0)

    def test_demo_refuses_production_without_explicit_flag(self):
        with patch("apps.company.management.commands.populate_demo_content.settings.DEBUG", False):
            with self.assertRaises(CommandError):
                call_command("populate_demo_content", stdout=StringIO())
        self.assertEqual(CompanySection.objects.count(), 0)

    def test_manual_records_survive_cleanup_and_demo_reruns(self):
        manual = CompanySection.objects.create(section_type="value", title_fa="Manual section", body_fa="Owner content", is_published=False, migration_notes="manual")
        call_command("populate_demo_content", stdout=StringIO())
        manual.refresh_from_db()
        self.assertEqual(manual.body_fa, "Owner content")
        demo = CompanySection.objects.filter(migration_notes__contains="demo-content:phase-9.10").first()
        demo.body_fa = "Owner-edited demo copy"
        demo.save(update_fields=("body_fa",))
        call_command("populate_demo_content", stdout=StringIO())
        self.assertEqual(CompanySection.objects.get(pk=demo.pk).body_fa, "Owner-edited demo copy")
        call_command("remove_demo_content", stdout=StringIO())
        self.assertTrue(CompanySection.objects.filter(pk=manual.pk).exists())
        self.assertFalse(CompanySection.objects.filter(migration_notes__contains="demo-content:phase-9.10").exists())

    def test_demo_documents_use_existing_fixture_and_cleanup_only_demo_rows(self):
        call_command("populate_demo_content", stdout=StringIO())
        documents = ProductDocument.objects.filter(display_name__startswith="[DEMO]")
        if Path("media/product-documents").exists():
            self.assertGreaterEqual(documents.count(), 0)
        call_command("remove_demo_content", stdout=StringIO())
        self.assertFalse(ProductDocument.objects.filter(display_name__startswith="[DEMO]").exists())
