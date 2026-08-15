from django.core.management.base import BaseCommand

from apps.company.models import Capability, CompanyCertification, CompanyHonor, CompanyLocation, CompanyMilestone, CompanySection, Industry
from apps.company.review import review_record


CONTENT_MODELS = (("CompanyLocation", CompanyLocation), ("CompanyMilestone", CompanyMilestone), ("CompanyCertification", CompanyCertification), ("CompanyHonor", CompanyHonor), ("Industry", Industry), ("CompanySection", CompanySection), ("Capability", Capability))


class Command(BaseCommand):
    help = "Print a read-only review report for company-content approval."

    def handle(self, *args, **options):
        records = []
        for kind, model in CONTENT_MODELS:
            for item in model.objects.all().order_by("pk"):
                records.append(review_record(kind, item))
        counts = {decision: sum(record["recommended_decision"] == decision for record in records) for decision in ("APPROVE", "EDIT", "VERIFY", "ARCHIVE", "KEEP DRAFT")}
        self.stdout.write("Mehrasl company content review (read-only)\n")
        self.stdout.write("Recommended decisions: " + ", ".join(f"{decision}={counts[decision]}" for decision in counts))
        for record in records:
            self.stdout.write("\n[{classification}] {kind} #{id}: {title}".format(**record))
            self.stdout.write(f"  source: {record['source_title'] or '-'} | {record['source_url'] or '-'}")
            if record["details"]:
                self.stdout.write("  details: " + "; ".join(f"{key}={value or '-'}" for key, value in record["details"].items()))
            self.stdout.write(f"  Persian: {record['persian'] or '-'}")
            self.stdout.write(f"  English: {record['english'] or '-'}")
            self.stdout.write(f"  verification: {record['verification']} | published: {record['published']}")
            self.stdout.write(f"  status: {record['status']} | verification_required: {record['verification_required']} | translation_required: {record['translation_required']} | editorial_required: {record['editorial_required']}")
            self.stdout.write(f"  missing: {', '.join(record['missing']) or '-'}")
            self.stdout.write(f"  decision: {record['recommended_decision']} | action: {record['recommended_action']}")
