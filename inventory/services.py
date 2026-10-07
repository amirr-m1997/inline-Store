"""سرویس انبار: اعمال تراکنش، رزرو، بررسی کمبود و پیشنهاد تأمین."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from core import audit
from core.models import AuditLog

from .models import PurchaseRequest, StockItem, StockMove


class InsufficientStock(Exception):
    """موجودی کافی برای رزرو وجود ندارد."""


@transaction.atomic
def apply_move(*, product, warehouse, kind: str, qty, unit_cost: int = 0, reference: str = "",
               order=None, note: str = "", user=None, counterparty: str = "") -> StockMove:
    """ثبت تراکنش انبار و به‌روزرسانی موجودی (با قفل رکورد)."""
    qty = Decimal(str(qty))
    item, _ = StockItem.objects.select_for_update().get_or_create(
        product=product, warehouse=warehouse
    )
    move = StockMove.objects.create(
        product=product, warehouse=warehouse, kind=kind, qty=qty, unit_cost=unit_cost,
        reference=reference, order=order, note=note, counterparty=counterparty,
    )
    if kind == "receipt":
        item.on_hand = F("on_hand") + qty
        item.incoming = F("incoming") - qty
        if float(item.incoming) < 0:
            item.incoming = Decimal("0")
    elif kind == "issue":
        item.on_hand = F("on_hand") - qty
    elif kind == "reserve":
        item.reserved = F("reserved") + qty
    elif kind == "release":
        item.reserved = F("reserved") - qty
        if float(item.reserved) < 0:
            item.reserved = Decimal("0")
    elif kind == "adjust":
        item.on_hand = F("on_hand") + qty  # qty می‌تواند منفی باشد
    elif kind == "return":
        item.on_hand = F("on_hand") + qty
    item.save()
    item.refresh_from_db()
    audit.log(
        action=AuditLog.Action.STOCK,
        instance=move,
        actor=user,
        note=f"{move.get_kind_display()} — موجودی جدید: {item.on_hand}",
        after={"on_hand": str(item.on_hand), "reserved": str(item.reserved)},
    )
    return move


def reserve_for_order(order, user=None) -> list[StockMove]:
    """رزرو موجودی ردیف‌های سفارش از انبار پیشنهادی هر ردیف."""
    moves: list[StockMove] = []
    for line in order.lines.select_related("product", "warehouse"):
        if line.qty_reserved:
            continue
        warehouse = line.warehouse or default_warehouse(line.product)
        if warehouse is None:
            continue
        item = StockItem.objects.filter(product=line.product, warehouse=warehouse).first()
        free = item.free_qty if item else 0
        qty = float(line.qty)
        if free < qty:
            # رزرو تا حد امکان + ثبت کسری
            reserve_qty = max(free, 0)
        else:
            reserve_qty = qty
        if reserve_qty:
            moves.append(apply_move(
                product=line.product, warehouse=warehouse, kind="reserve", qty=reserve_qty,
                reference=order.number, order=order, user=user,
                note=f"رزرو برای سفارش {order.number}",
            ))
        line.qty_reserved = Decimal(str(reserve_qty))
        line.warehouse = warehouse
        line.save(update_fields=["qty_reserved", "warehouse"])
    return moves


def release_for_order(order, user=None) -> list[StockMove]:
    """آزادسازی رزروها (لغو سفارش)."""
    moves = []
    for line in order.lines.select_related("product", "warehouse"):
        if not line.qty_reserved or not line.warehouse:
            continue
        moves.append(apply_move(
            product=line.product, warehouse=line.warehouse, kind="release",
            qty=line.qty_reserved, reference=order.number, order=order, user=user,
            note=f"آزادسازی رزرو سفارش {order.number}",
        ))
        line.qty_reserved = Decimal("0")
        line.save(update_fields=["qty_reserved"])
    return moves


def default_warehouse(product=None):
    from .models import Warehouse

    return Warehouse.objects.filter(is_active=True).order_by("code").first()


def stock_check(product, qty, warehouse=None) -> dict:
    """بررسی موجودی برای یک درخواست: کافی / ناکافی / نیاز به تأمین."""
    item = None
    if warehouse is not None:
        item = StockItem.objects.filter(product=product, warehouse=warehouse).first()
    if item is None:
        item = StockItem.objects.filter(product=product).order_by("-on_hand").first()
    free = item.free_qty if item else 0
    shortage = max(float(qty) - free, 0)
    return {
        "product": product,
        "requested": float(qty),
        "free": free,
        "incoming": float(item.incoming) if item else 0,
        "lead_time_days": product.lead_time_days,
        "shortage": shortage,
        "sufficient": shortage == 0,
        "warehouse": item.warehouse if item else None,
        "suggested_purchase": product.apply_packaging(shortage) if shortage else 0,
    }


def low_stock_items(limit: int | None = None):
    """اقلامی که به نقطه سفارش رسیده‌اند یا کسری رزرو دارند."""
    qs = (
        StockItem.objects.select_related("product", "warehouse")
        .filter(product__is_active=True)
        .order_by("on_hand")
    )
    rows = [item for item in qs if item.status[0] in ("critical", "low", "out", "error")]
    return rows[:limit] if limit else rows


def create_purchase_requests_for_low_stock(user=None) -> list[PurchaseRequest]:
    """ساخت پیش‌نویس درخواست خرید برای اقلام زیر نقطه سفارش (اتوماسیون)."""
    created = []
    for item in low_stock_items():
        shortage = item.shortage_to_reorder
        if shortage <= 0:
            continue
        exists = PurchaseRequest.objects.filter(
            product=item.product, warehouse=item.warehouse,
            status__in=["draft", "submitted", "approved", "ordered"],
        ).exists()
        if exists:
            continue
        created.append(PurchaseRequest.objects.create(
            product=item.product, warehouse=item.warehouse,
            qty=item.product.apply_packaging(shortage),
            status="submitted", requested_by=user,
            estimated_cost=int(shortage * item.unit_cost),
            note="ایجاد خودکار به‌دلیل رسیدن به نقطه سفارش",
        ))
    return created
