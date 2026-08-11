from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.pricing.models import Currency, ProductPrice


class Command(BaseCommand):
    help = "Create one identifiable sample product under every active root category."

    @staticmethod
    def first_leaf(root):
        frontier = list(Category.objects.filter(parent=root, is_active=True).order_by("code", "id"))
        while frontier:
            category = frontier.pop(0)
            children = list(Category.objects.filter(parent=category, is_active=True).order_by("code", "id"))
            if not children:
                return category
            frontier[0:0] = children
        return root

    def handle(self, *args, **options):
        counts = {"products_created": 0, "products_updated": 0, "roots_covered": 0}
        roots = Category.objects.filter(parent=None, is_active=True).order_by("code", "id")

        with transaction.atomic():
            for index, root in enumerate(roots, start=1):
                leaf = self.first_leaf(root)
                code = f"SAMPLE-CAT-{int(root.code):02d}" if root.code.isdigit() else f"SAMPLE-CAT-{root.id}"
                product, created = Product.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": f"محصول نمونه {leaf.name_fa}",
                        "slug": f"sample-category-{root.id}",
                        "category": leaf,
                        "unit": "عدد",
                        "description": f"محصول نمونه برای بررسی مسیر دسته‌بندی «{root.name_fa}» تا «{leaf.name_fa}».",
                        "technical_specs": {"نوع داده": "نمونه آزمایشی", "دسته اصلی": root.name_fa, "دسته نهایی": leaf.name_fa},
                        "is_active": True,
                    },
                )
                counts["products_created" if created else "products_updated"] += 1
                counts["roots_covered"] += 1
                Inventory.objects.update_or_create(
                    product=product,
                    defaults={"on_hand_quantity": 10 + index, "reserved_quantity": index % 3},
                )
                ProductPrice.objects.update_or_create(
                    product=product,
                    source="category_sample_seed",
                    defaults={
                        "amount": Decimal(500000 + index * 125000),
                        "discount_percentage": Decimal("10.00") if index % 3 == 0 else Decimal("0.00"),
                        "currency": Currency.IRR,
                        "effective_from": timezone.now(),
                        "effective_to": None,
                    },
                )
                self.stdout.write(f"{root.name_fa} -> {leaf.name_fa} -> {product.code}")

        self.stdout.write(self.style.SUCCESS(", ".join(f"{key}={value}" for key, value in counts.items())))
