import csv
from django.core.management.base import BaseCommand

from apps.content.models import ContentArticle, FAQEntry
from apps.content.review import duplicate_index, evaluate_record


class Command(BaseCommand):
    help = "Export a read-only editorial review CSV."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="Output CSV path; stdout is used when omitted.")

    def handle(self, *args, **options):
        destination = open(options["output"], "w", encoding="utf-8", newline="") if options.get("output") else self.stdout
        try:
            articles = list(ContentArticle.objects.all().prefetch_related("products", "catalog_categories", "brands", "industries", "capabilities"))
            faqs = list(FAQEntry.objects.all().prefetch_related("products", "categories", "industries", "capabilities", "articles"))
            all_items = articles + faqs
            index = duplicate_index(all_items)
            writer = csv.DictWriter(destination, fieldnames=("model", "id", "slug", "title_or_question", "content_type", "is_active", "is_published", "published_at", "review_status", "provenance_type", "source_url", "source_title", "missing_fields", "quality_flags", "related_products", "related_categories", "related_brands", "related_industries", "related_capabilities", "duplicate_candidates", "recommended_action"))
            writer.writeheader()
            for item in all_items:
                review = evaluate_record(item, index)
                categories = item.catalog_categories if isinstance(item, ContentArticle) else item.categories
                writer.writerow({
                    "model": review["model"], "id": item.pk, "slug": item.slug, "title_or_question": review["title"], "content_type": review["content_type"],
                    "is_active": item.is_active, "is_published": item.is_published, "published_at": item.published_at.isoformat() if item.published_at else "", "review_status": review["review_status"],
                    "provenance_type": "demo" if review["is_demo"] else "imported" if review["is_imported"] else "manual", "source_url": item.source_url, "source_title": item.source_title,
                    "missing_fields": ";".join(review["missing"]), "quality_flags": ";".join(review["warnings"]),
                    "related_products": ";".join(str(x) for x in item.products.values_list("slug", flat=True)),
                    "related_categories": ";".join(str(x) for x in categories.values_list("slug", flat=True)),
                    "related_brands": ";".join(str(x) for x in item.brands.values_list("slug", flat=True)) if isinstance(item, ContentArticle) else "",
                    "related_industries": ";".join(str(x) for x in item.industries.values_list("slug", flat=True)),
                    "related_capabilities": ";".join(str(x) for x in item.capabilities.values_list("slug", flat=True)),
                    "duplicate_candidates": ";".join(review["duplicate_candidates"]),
                    "recommended_action": review["recommended_action"],
                })
        finally:
            if options.get("output"):
                destination.close()
