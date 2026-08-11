import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory


class Command(BaseCommand):
    help = "Imports the LOCAL_SHOP reference catalog without moving its browser architecture into production."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[5] / "LOCAL_SHOP" / "local_shop.html")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        source = options["source"]
        if not source.is_file():
            raise CommandError(f"Demo source does not exist: {source}")
        payload = self.read_payload(source)
        report = {"categories": 0, "products": 0, "inventories": 0, "category_exceptions": 0, "inventory_exceptions": 0}
        with transaction.atomic():
            category_map = self.import_categories(payload["tree"], report)
            self.import_products(payload["products"], category_map, report)
            if options["dry_run"]:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS("Imported reference catalog: " + ", ".join(f"{key}={value}" for key, value in report.items())))

    @staticmethod
    def read_payload(source):
        text = source.read_text(encoding="utf-8")
        prefix = "const DATA = "
        try:
            start = text.index(prefix) + len(prefix)
            return json.JSONDecoder().raw_decode(text[start:])[0]
        except (ValueError, json.JSONDecodeError) as error:
            raise CommandError("Could not parse const DATA from the reference demo") from error

    def import_categories(self, tree, report):
        category_map = {}
        for type_data in tree:
            type_code = str(type_data["code"])
            root, created = Category.objects.update_or_create(
                parent=None, code=type_code,
                defaults={"name_fa": type_data["name"], "name_en": "", "slug": f"type-{type_code}", "is_active": True},
            )
            report["categories"] += int(created)
            category_map[(type_data["code"], None, None)] = root
            for group_data in type_data["groups"]:
                group_code = str(group_data["code"])
                group, created = Category.objects.update_or_create(
                    parent=root, code=group_code,
                    defaults={"name_fa": group_data["name"], "name_en": "", "slug": f"type-{type_code}-group-{group_code}", "is_active": True},
                )
                report["categories"] += int(created)
                category_map[(type_data["code"], group_data["code"], None)] = group
                for subgroup_data in group_data["subs"]:
                    subgroup_code = str(subgroup_data["code"])
                    subgroup, created = Category.objects.update_or_create(
                        parent=group, code=subgroup_code,
                        defaults={"name_fa": subgroup_data["name"], "name_en": "", "slug": f"type-{type_code}-group-{group_code}-subgroup-{subgroup_code}", "is_active": True},
                    )
                    report["categories"] += int(created)
                    category_map[(type_data["code"], group_data["code"], subgroup_data["code"])] = subgroup
        return category_map

    def import_products(self, products, category_map, report):
        existing_codes = set(Product.objects.filter(code__in=[str(item["code"]) for item in products]).values_list("code", flat=True))
        new_products = []
        inventory_rows = []
        for item in products:
            category = category_map.get((item["t"], item["g"], item["z"]))
            if category is None:
                # The reference contains a few product paths absent from its own tree.
                # Retain the exact supplied tree and attach those products at their known group.
                category = category_map.get((item["t"], item["g"], None))
                report["category_exceptions"] += 1
            if category is None:
                raise CommandError(f"Product {item['code']} has no matching category path")
            code = str(item["code"])
            if code in existing_codes:
                product = Product.objects.get(code=code)
            else:
                product = Product(code=code, name=item["name"], slug=f"demo-{code}", category=category, unit=item.get("unit") or "", is_active=True)
                new_products.append(product)
                continue
            self.add_inventory(product, item, inventory_rows, report)
        Product.objects.bulk_create(new_products, batch_size=500)
        report["products"] += len(new_products)
        created = Product.objects.filter(code__in=[product.code for product in new_products]).only("id", "code")
        source_by_code = {str(item["code"]): item for item in products}
        for product in created:
            self.add_inventory(product, source_by_code[product.code], inventory_rows, report)
        Inventory.objects.bulk_create(inventory_rows, ignore_conflicts=True, batch_size=500)
        report["inventories"] += len(inventory_rows)

    @staticmethod
    def add_inventory(product, item, inventory_rows, report):
        on_hand, reserved = item.get("inv"), item.get("res")
        if not isinstance(on_hand, (int, float)) or not isinstance(reserved, (int, float)) or on_hand < 0 or reserved < 0 or reserved > on_hand:
            report["inventory_exceptions"] += 1
            return
        if not float(on_hand).is_integer() or not float(reserved).is_integer():
            report["inventory_exceptions"] += 1
            return
        inventory_rows.append(Inventory(product=product, on_hand_quantity=int(on_hand), reserved_quantity=int(reserved)))
