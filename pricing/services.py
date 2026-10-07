"""موتور قیمت‌گذاری: تعیین قیمت واحد بر اساس مشتری، سبد قیمت و تعداد."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.utils import timezone

from .models import PriceListItem, QuantityPriceBreak


@dataclass
class PriceResult:
    """نتیجه‌ی تعیین قیمت برای یک ردیف سفارش/استعلام."""

    product: object
    list_price: int          # قیمت پایه کالا
    unit_price: int          # قیمت واحد نهایی برای این مشتری/تعداد
    base_for_tier: int       # قیمتی که پله‌ها روی آن اعمال شده
    source: str              # عمومی | سبد قیمت | پله حجمی | تخفیف اختصاصی
    price_list: object | None = None
    tier: object | None = None
    discount_pct: float = 0.0

    @property
    def discount_amount(self) -> int:
        return max(self.list_price - self.unit_price, 0)

    @property
    def total_discount_pct(self) -> float:
        if not self.list_price:
            return 0.0
        return round(self.discount_amount * 100 / self.list_price, 2)


def resolve_price(product, company=None, qty: float = 1, day=None) -> PriceResult:
    """قیمت واحد کالا برای مشتری و تعداد مشخص را تعیین می‌کند.

    ترتیب اولویت:
    ۱) قیمت اختصاصی کالا در سبد قیمت مشتری
    ۲) درصد تخفیف عمومی سبد قیمت
    ۳) قیمت پایه
    سپس پله‌های حجمی همان سبد (یا سبد عمومی) اعمال می‌شود.
    """
    day = day or timezone.localdate()
    qty = float(qty or 0)
    list_price = int(product.base_price or 0)
    price_list = getattr(company, "price_list", None) if company is not None else None
    source = "قیمت پایه"
    base_for_tier = list_price
    item = None

    if price_list is not None:
        item = (
            PriceListItem.objects.filter(price_list=price_list, product=product)
            .order_by("-valid_until")
            .first()
        )
        if item and item.is_valid_on(day) and item.price:
            base_for_tier = int(item.price)
            source = f"سبد قیمت «{price_list.name}»"
        elif price_list.discount_pct:
            base_for_tier = int(round(list_price * (1 - float(price_list.discount_pct) / 100)))
            source = f"تخفیف سبد «{price_list.name}»"

    tier = None
    tier_qs = QuantityPriceBreak.objects.filter(product=product, min_qty__lte=qty)
    if price_list is not None:
        scoped = tier_qs.filter(price_list=price_list)
        tier = scoped.order_by("-min_qty").first()
    if tier is None:
        tier = tier_qs.filter(price_list__kind="list").order_by("-min_qty").first()

    unit_price = base_for_tier
    if tier is not None:
        unit_price = tier.unit_price(base_for_tier)
        threshold = int(tier.min_qty) if float(tier.min_qty).is_integer() else tier.min_qty
        source = f"{source} + پله {threshold}+"

    discount_pct = round((list_price - unit_price) * 100 / list_price, 2) if list_price else 0.0
    return PriceResult(
        product=product,
        list_price=list_price,
        unit_price=int(unit_price),
        base_for_tier=base_for_tier,
        source=source,
        price_list=price_list,
        tier=tier,
        discount_pct=discount_pct,
    )


def price_levels_for(product, company=None, quantities=(1, 3, 5, 10, 30, 100)) -> list[dict]:
    """جدول پله‌های قیمت یک کالا برای نمایش در پنل."""
    rows = []
    for qty in quantities:
        result = resolve_price(product, company=company, qty=qty)
        rows.append({"qty": qty, "unit_price": result.unit_price,
                     "discount_pct": result.total_discount_pct, "source": result.source})
    return rows


def expiring_lists(days: int = 14):
    """سبدهای قیمت در آستانه‌ی انقضا."""
    today = timezone.localdate()
    return [
        pl for pl in PriceList_objects()
        if pl.is_active and pl.valid_until and 0 <= (pl.valid_until - today).days <= days
    ]


def PriceList_objects():
    from .models import PriceList

    return PriceList.objects.all()
