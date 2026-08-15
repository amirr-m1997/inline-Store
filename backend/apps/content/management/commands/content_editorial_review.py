from collections import Counter

from django.core.management.base import BaseCommand

from apps.content.models import ContentArticle, FAQEntry
from apps.content.review import duplicate_groups, duplicate_index, evaluate_record


class Command(BaseCommand):
    help = "Read-only editorial quality and provenance review for articles and FAQs."

    def handle(self, *args, **options):
        articles = list(ContentArticle.objects.all().prefetch_related("products", "catalog_categories", "brands", "industries", "capabilities"))
        faqs = list(FAQEntry.objects.all().prefetch_related("products", "categories", "industries", "capabilities", "articles"))
        all_items = articles + faqs
        index = duplicate_index(all_items)
        records = [evaluate_record(item, index) for item in all_items]
        counts = Counter()
        for item, record in zip(all_items, records):
            counts["demo"] += int(record["is_demo"])
            counts["published"] += int(record["is_published"])
            counts["unpublished"] += int(not record["is_published"])
            counts["active"] += int(item.is_active)
            counts["imported"] += int(record["is_imported"])
            counts["manual"] += int(not record["is_imported"] and not record["is_demo"])
            counts["drafts"] += int(record["review_status"] == "draft")
            counts["missing_english"] += int(any(field.endswith("_en") for field in record["missing"]))
            counts["missing_seo"] += int(any(field.startswith("seo_") for field in record["missing"]))
            counts["missing_source"] += int("source_url" in record["missing"])
            counts["missing_image"] += int("featured_image" in record["missing"])
            counts["missing_relationships"] += int("relationships" in record["missing"])
            counts["future_dated"] += int("future_publication" in record["warnings"])
            counts["duplicate_candidates"] += int(bool(record["duplicate_candidates"]))
            counts["recommended_review"] += int(record["recommended_action"] == "manual_review")
        self.stdout.write("Editorial content review (read-only)")
        self.stdout.write(f"total articles: {len(articles)}")
        self.stdout.write(f"total FAQs: {len(faqs)}")
        for key in ("active", "published", "unpublished", "drafts", "demo", "imported", "manual", "missing_english", "missing_seo", "missing_image", "missing_source", "missing_relationships", "future_dated", "duplicate_candidates", "recommended_review"):
            self.stdout.write(f"{key}: {counts[key]}")
        duplicates = duplicate_groups(articles + faqs)
        self.stdout.write(f"duplicate signals: {len(duplicates)}")
        for record in records:
            if record["recommended_action"] == "manual_review":
                self.stdout.write(f"review: {record['model']}#{record['id']} {record['title']} | missing={','.join(record['missing']) or '-'} | warnings={','.join(record['warnings']) or '-'} | duplicates={','.join(record['duplicate_candidates']) or '-'}")
