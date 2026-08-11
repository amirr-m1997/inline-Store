from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.pricing.models import Currency, ProductPrice


CATALOG = [
    ("demo-materials", "مواد اولیه تولید", [
        ("fasteners", "پیچ و اتصالات", [("allen", "پیچ آلن"), ("hex-bolts", "پیچ شش گوش")]),
        ("nuts", "مهره‌ها", [("hex-nuts", "مهره شش گوش")]),
        ("washers", "واشرها", [("flat-washers", "واشر تخت")]),
    ]),
    ("demo-industrial", "قطعات صنعتی", [
        ("bearings", "یاتاقان‌ها", [("ball-bearings", "بلبرینگ صنعتی"), ("roller-bearings", "رولبرینگ")]),
    ]),
    ("demo-tools", "ابزارآلات", [
        ("hand-tools", "ابزار دستی", [("wrenches", "آچار"), ("screwdrivers", "پیچ گوشتی")]),
    ]),
    ("demo-controls", "تجهیزات کنترل", [
        ("measurement", "اندازه‌گیری", [("thermometers", "دماسنج صنعتی"), ("pressure-gauges", "گیج فشار")]),
    ]),
]


class Command(BaseCommand):
    help = "Creates an idempotent, Persian, database-backed catalog demo."

    def handle(self, *args, **options):
        counts = {"categories": 0, "products": 0, "inventories": 0, "prices": 0}
        with transaction.atomic():
            for root_code, root_name, groups in CATALOG:
                root = self.upsert_category(None, root_code, root_name, f"catalog-{root_code}", counts)
                for group_code, group_name, leaves in groups:
                    group = self.upsert_category(root, group_code, group_name, f"{root.slug}-{group_code}", counts)
                    for leaf_code, leaf_name in leaves:
                        leaf = self.upsert_category(group, leaf_code, leaf_name, f"{group.slug}-{leaf_code}", counts)
                        self.seed_leaf_products(leaf, counts)
        self.stdout.write(self.style.SUCCESS("Catalog demo seeded: " + ", ".join(f"{key}={value}" for key, value in counts.items())))

    @staticmethod
    def upsert_category(parent, code, name, slug, counts):
        category, created = Category.objects.update_or_create(
            parent=parent,
            code=code,
            defaults={"name_fa": name, "name_en": "", "slug": slug, "is_active": True},
        )
        counts["categories"] += int(created)
        return category

    @staticmethod
    def seed_leaf_products(category, counts):
        for number in (1, 2):
            code = f"DEMO-{category.code.upper()}-{number:03d}"
            product, created = Product.objects.update_or_create(
                code=code,
                defaults={
                    "name": f"{category.name_fa} صنعتی مدل {number}",
                    "slug": f"{category.slug}-model-{number}",
                    "category": category,
                    "unit": "عدد",
                    "description": f"نمونه کالای ثبت‌شده در دیتابیس برای دسته {category.name_fa}.",
                    "technical_specs": {"کاربری": "صنعتی", "دسته": category.name_fa, "مدل": str(number)},
                    "is_active": True,
                },
            )
            counts["products"] += int(created)
            _, inventory_created = Inventory.objects.update_or_create(
                product=product,
                defaults={"on_hand_quantity": number * 12, "reserved_quantity": number - 1},
            )
            counts["inventories"] += int(inventory_created)
            _, price_created = ProductPrice.objects.update_or_create(
                product=product,
                effective_from__lte=timezone.now(),
                effective_to__isnull=True,
                defaults={"amount": number * 1000000, "currency": Currency.IRR, "discount_percentage": 10 if number == 1 else 0, "effective_from": timezone.now(), "source": "seed_catalog_demo"},
            )
            counts["prices"] += int(price_created)
