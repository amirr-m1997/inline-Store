import csv

from django.core.management.base import BaseCommand

from apps.company.management.commands.content_review_report import CONTENT_MODELS
from apps.company.review import review_record


FIELDS = ("content_type", "record_id", "persian_title", "english_title", "source_url", "status", "verification_required", "translation_required", "editorial_required", "missing_information", "recommended_decision", "business_decision", "business_notes")


class Command(BaseCommand):
    help = "Export a read-only CSV approval sheet for company content."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Optional CSV path; defaults to stdout.")

    def handle(self, *args, **options):
        stream = open(options["output"], "w", newline="", encoding="utf-8-sig") if options.get("output") else self.stdout
        try:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for kind, model in CONTENT_MODELS:
                for item in model.objects.all().order_by("pk"):
                    record = review_record(kind, item)
                    writer.writerow({"content_type": record["kind"], "record_id": record["id"], "persian_title": record["title"], "english_title": record["english_title"], "source_url": record["source_url"], "status": record["status"], "verification_required": record["verification_required"], "translation_required": record["translation_required"], "editorial_required": record["editorial_required"], "missing_information": "; ".join(record["missing"]), "recommended_decision": record["recommended_decision"], "business_decision": "", "business_notes": ""})
        finally:
            if options.get("output"):
                stream.close()
