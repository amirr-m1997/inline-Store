from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, CategorySlugRedirect
from apps.catalog.slugs import latin_category_slug


class Command(BaseCommand):
    help = "Replace positional category slugs with stable Latin slugs and retain legacy mappings."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        categories = list(Category.objects.order_by("id"))
        targets = [item for item in categories if item.slug.startswith("category-")]
        used = {item.slug for item in categories if item not in targets}
        changes = []
        for category in targets:
            base = latin_category_slug(category.name_fa)
            candidate, suffix = base, 2
            while candidate in used:
                candidate, suffix = f"{base}-{suffix}", suffix + 1
            used.add(candidate)
            changes.append((category, category.slug, candidate))

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write(f"Would update {len(changes)} categories.")
            return

        for category, old_slug, _ in changes:
            CategorySlugRedirect.objects.update_or_create(old_slug=old_slug, defaults={"category": category})
            category.slug = f"pending-slug-{category.pk}"
        Category.objects.bulk_update([item[0] for item in changes], ["slug"])
        for category, _, new_slug in changes:
            category.slug = new_slug
        Category.objects.bulk_update([item[0] for item in changes], ["slug"])
        self.stdout.write(self.style.SUCCESS(f"Updated {len(changes)} category slugs; legacy redirects={len(changes)}"))
