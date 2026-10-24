"""Price resolution shared by cart and checkout.

The public catalog price remains the fallback.  A signed-in customer can receive
an active contract tier when the cart quantity meets its minimum quantity.
"""

from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import CustomerPriceListItem, ProductPrice


def _price_payload(original_amount, final_amount, currency, discount_percentage, *, price_list_name=None):
    payload = {
        "original_amount": str(original_amount),
        "currency": currency,
        "discount_percentage": str(discount_percentage),
        "final_amount": str(final_amount.quantize(Decimal("0.01"))),
    }
    if price_list_name:
        payload["price_list"] = price_list_name
        payload["is_contract_price"] = True
    return payload


def bulk_price_map(product_quantities, customer=None):
    """Return one effective price per product without a query per cart row."""
    quantities = {}
    for row in product_quantities:
        if isinstance(row, tuple):
            product_id, quantity = row
        else:
            product_id, quantity = row, 1
        if product_id is not None:
            quantities[product_id] = max(int(quantity or 1), 1)
    if not quantities:
        return {}

    now = timezone.now()
    base_rows = (
        ProductPrice.objects.filter(product_id__in=quantities, effective_from__lte=now)
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=now))
        .order_by("product_id", "-effective_from")
    )
    resolved = {}
    for row in base_rows:
        if row.product_id in resolved:
            continue
        final = row.amount * (Decimal("1") - row.discount_percentage / Decimal("100"))
        resolved[row.product_id] = _price_payload(
            row.amount, final, row.currency, row.discount_percentage,
        )

    if not customer or not getattr(customer, "is_authenticated", False):
        return resolved

    contract_rows = (
        CustomerPriceListItem.objects.filter(
            product_id__in=quantities,
            price_list__customer=customer,
            price_list__is_active=True,
            price_list__valid_from__lte=now,
        )
        .filter(Q(price_list__valid_until__isnull=True) | Q(price_list__valid_until__gte=now))
        .select_related("price_list")
        .order_by("product_id", "-price_list__priority", "-minimum_quantity", "-id")
    )
    selected = {}
    for item in contract_rows:
        product_id = item.product_id
        if product_id in selected or item.minimum_quantity > quantities[product_id]:
            continue
        selected[product_id] = item

    for product_id, item in selected.items():
        base = resolved.get(product_id)
        if item.fixed_amount is not None:
            original = Decimal(base["original_amount"]) if base else item.fixed_amount
            final = item.fixed_amount
            discount = (
                max(Decimal("0"), (Decimal("1") - final / original) * Decimal("100"))
                if original else Decimal("0")
            )
        elif base:
            original = Decimal(base["original_amount"])
            discount = item.discount_percentage
            final = original * (Decimal("1") - discount / Decimal("100"))
        else:
            # A percentage contract has no meaning when the public base price is missing.
            continue
        resolved[product_id] = _price_payload(
            original, final, base["currency"] if base else item.price_list.currency,
            discount, price_list_name=item.price_list.name,
        )
    return resolved
