import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Category


class Command(BaseCommand):
    help = "Import the complete category tree from the original LOCAL_SHOP demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=settings.BASE_DIR.parent / "LOCAL_SHOP" / "local_shop.html",
            help="Path to the original LOCAL_SHOP HTML demo.",
        )

    def handle(self, *args, **options):
        source = options["source"]
        tree = self.read_tree(source)
        created = updated = 0

        for root_data in tree:
            root, was_created = self.upsert_category(root_data, parent=None, path=[])
            created += was_created
            updated += not was_created
            for group_data in root_data.get("groups", []):
                group, was_created = self.upsert_category(group_data, parent=root, path=[root.code])
                created += was_created
                updated += not was_created
                for leaf_data in group_data.get("subs", []):
                    _, was_created = self.upsert_category(leaf_data, parent=group, path=[root.code, group.code])
                    created += was_created
                    updated += not was_created

        categories = Category.objects.all()
        self.stdout.write(self.style.SUCCESS(
            "Imported category tree: "
            f"total={categories.count()}, created={created}, updated={updated}, "
            f"roots={categories.filter(parent=None).count()}, max_depth={max(categories.values_list('level', flat=True), default=0)}"
        ))

    @staticmethod
    def read_tree(source):
        if not source.is_file():
            raise CommandError(f"Original demo source does not exist: {source}")
        text = source.read_text(encoding="utf-8")
        marker = "const DATA = "
        try:
            payload = json.JSONDecoder().raw_decode(text[text.index(marker) + len(marker):])[0]
            return payload["tree"]
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            raise CommandError("Could not read the category tree from the original demo") from error

    @staticmethod
    def upsert_category(data, parent, path):
        code = str(data["code"])
        category, created = Category.objects.get_or_create(
            parent=parent,
            code=code,
            defaults={
                "name_fa": data["name"],
                "name_en": "",
                "slug": "",
                "is_active": True,
            },
        )
        if not created:
            category.name_fa = data["name"]
            category.is_active = True
            category.save(update_fields=("name_fa", "is_active", "level", "updated_at"))
        return category, created
