from django.db.models import Count, F, IntegerField, Min, Q, ExpressionWrapper
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory, Issue, Receipt


def _product_row(product):
    return {
        "code": product.code,
        "name": product.name,
        "category": product.category.name_fa if product.category_id else None,
        "on_hand": product.on_hand_quantity,
        "reserved": product.reserved_quantity,
        "available": product.available_quantity,
    }


def _annotated_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related("category", "inventory")
        .annotate(
            on_hand_quantity=F("inventory__on_hand_quantity"),
            reserved_quantity=F("inventory__reserved_quantity"),
            available_quantity=ExpressionWrapper(
                F("inventory__on_hand_quantity") - F("inventory__reserved_quantity"),
                output_field=IntegerField(),
            ),
        )
    )


def _oldest_movement(model, field_name):
    aggregates = model.objects.values("product_id").annotate(first_at=Min("occurred_at")).order_by("first_at")[:10]
    product_ids = [row["product_id"] for row in aggregates]
    names = {product.id: product for product in Product.objects.filter(id__in=product_ids).select_related("category")}
    return [
        {
            "code": names[row["product_id"]].code if row["product_id"] in names else None,
            "name": names[row["product_id"]].name if row["product_id"] in names else None,
            "first_at": row["first_at"].isoformat(),
        }
        for row in aggregates
        if row["product_id"] in names
    ]


def build_dashboard_payload():
    products = _annotated_products()
    level_counts = dict(
        Category.objects.filter(is_active=True).values_list("level").annotate(count=Count("id"))
    )
    never_issued_ids = Product.objects.filter(is_active=True).exclude(id__in=Issue.objects.values("product_id")).values_list("id", flat=True)
    never_issued = products.filter(id__in=never_issued_ids).order_by("-on_hand_quantity")[:10]

    top_categories = list(
        Category.objects.filter(is_active=True)
        .annotate(product_count=Count("products"))
        .order_by("-product_count")[:10]
    )

    return {
        "kpis": {
            "total_products": products.count(),
            "total_categories": Category.objects.filter(is_active=True).count(),
            "types": level_counts.get(0, 0),
            "groups": level_counts.get(1, 0),
            "subgroups": level_counts.get(2, 0),
            "products_with_stock": Inventory.objects.filter(on_hand_quantity__gt=0).count(),
            "products_with_reservations": Inventory.objects.filter(reserved_quantity__gt=0).count(),
        },
        "top_10": {
            "by_stock": [_product_row(item) for item in products.order_by("-on_hand_quantity")[:10]],
            "by_reserved": [_product_row(item) for item in products.order_by("-reserved_quantity")[:10]],
            "by_available": [_product_row(item) for item in products.order_by("-available_quantity")[:10]],
            "never_issued": [_product_row(item) for item in never_issued],
            "oldest_receipts": _oldest_movement(Receipt, "occurred_at"),
            "oldest_issues": _oldest_movement(Issue, "occurred_at"),
            "top_categories": [
                {"id": item.id, "name_fa": item.name_fa, "product_count": item.product_count}
                for item in top_categories
            ],
        },
        "generated_at": timezone.now().isoformat(),
    }