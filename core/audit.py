"""سرویس لاگ حسابرسی + ثبت خودکار تغییرات مدل‌های حساس."""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Iterable

from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save

from .models import AuditLog

# ------------------------------------------------------------------ کمکی‌ها


def _serialize(value: Any):
    """تبدیل مقدار به JSON قابل ذخیره."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, models.Model):
        return str(value)
    return str(value)


def _snapshot(instance, fields: Iterable[str]) -> dict:
    data = {}
    for field in fields:
        if hasattr(instance, f"{field}_id"):  # کلید خارجی
            data[field] = _serialize(getattr(instance, f"{field}_id"))
        else:
            data[field] = _serialize(getattr(instance, field, None))
    return data


def client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log(
    *,
    action: str,
    instance=None,
    model_name: str | None = None,
    object_id: str | None = None,
    object_repr: str | None = None,
    before=None,
    after=None,
    changed_fields=None,
    actor=None,
    reason: str = "",
    note: str = "",
    request=None,
) -> AuditLog | None:
    """ثبت یک رخداد در لاگ حسابرسی."""
    from .middleware import get_current_user

    request = request or getattr(_thread_request, "value", None)
    user = actor or get_current_user(request)
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None

    role = ""
    if user is not None:
        profile = getattr(user, "profile", None)
        role = profile.get_role_display() if profile else ""

    if model_name is None and instance is not None:
        model_name = f"{instance._meta.app_label}.{instance._meta.model_name}"
    if object_id is None and instance is not None and instance.pk is not None:
        object_id = str(instance.pk)
    if object_repr is None and instance is not None:
        object_repr = str(instance)[:255]

    return AuditLog.objects.create(
        action=action,
        actor=user,
        actor_repr=(getattr(user, "get_full_name", lambda: "")() or getattr(user, "username", ""))[:120]
        if user
        else "سیستم",
        role=role,
        model_name=model_name or "",
        object_id=str(object_id or ""),
        object_repr=object_repr or "",
        before=before,
        after=after,
        changed_fields=changed_fields,
        reason=reason,
        note=note,
        ip=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:500] if request else ""),
    )


class _ThreadRequest:
    value = None


_thread_request = _ThreadRequest()


def set_current_request(request):
    _thread_request.value = request


def get_current_request():
    return _thread_request.value


# ------------------------------------------------- ثبت خودکار تغییرات مدل


class TrackedModelMeta:
    """میکسین: تغییرات فیلدهای مشخص را خودکار در لاگ حسابرسی ثبت می‌کند."""

    audit_fields: tuple[str, ...] = ()
    audit_action = AuditLog.Action.UPDATE

    @classmethod
    def audit_watch(cls) -> tuple[str, ...]:
        return cls.audit_fields


def track(model: type[models.Model], fields: tuple[str, ...], action: str | None = None,
          reason_field: str | None = None):
    """ثبت سیگنال‌های pre_save/post_save/post_delete برای یک مدل."""
    label = f"{model._meta.app_label}.{model._meta.model_name}"
    if label in _TRACKED:
        return
    _TRACKED[label] = (model, fields, action, reason_field)

    def _pre_save(sender, instance, **kwargs):
        if instance.pk:
            try:
                old = sender.objects.get(pk=instance.pk)
            except sender.DoesNotExist:
                return
            instance._audit_before = _snapshot(old, fields)  # type: ignore[attr-defined]

    def _post_save(sender, instance, created, **kwargs):
        before = getattr(instance, "_audit_before", None)
        after = _snapshot(instance, fields)
        if created:
            log(
                action=AuditLog.Action.CREATE,
                instance=instance,
                before=None,
                after=after,
                changed_fields=list(after.keys()),
            )
            return
        if before is None:
            return
        changed = [key for key in after if before.get(key) != after.get(key)]
        if not changed:
            return
        detected_action = action or AuditLog.Action.UPDATE
        field_map = {"price": AuditLog.Action.PRICE, "amount": AuditLog.Action.PRICE}
        if detected_action == AuditLog.Action.UPDATE and any(
            f in ("price", "base_price", "offered_price", "unit_price") for f in changed
        ):
            detected_action = AuditLog.Action.PRICE
        if detected_action == AuditLog.Action.UPDATE and any(
            f.startswith(("on_hand", "reserved", "incoming", "qty")) for f in changed
        ):
            detected_action = AuditLog.Action.STOCK
        if detected_action == AuditLog.Action.UPDATE and "status" in changed:
            detected_action = AuditLog.Action.STATUS
        log(
            action=detected_action,
            instance=instance,
            before={k: before.get(k) for k in changed},
            after={k: after.get(k) for k in changed},
            changed_fields=changed,
            reason=getattr(instance, reason_field, "") if reason_field else "",
        )

    def _post_delete(sender, instance, **kwargs):
        log(
            action=AuditLog.Action.DELETE,
            instance=instance,
            before=_snapshot(instance, fields),
            after=None,
        )

    pre_save.connect(_pre_save, sender=model, dispatch_uid=f"audit_pre_{label}")
    post_save.connect(_post_save, sender=model, dispatch_uid=f"audit_post_{label}")
    post_delete.connect(_post_delete, sender=model, dispatch_uid=f"audit_delete_{label}")


_TRACKED: dict[str, tuple] = {}


def tracked_models() -> dict:
    return _TRACKED


def track_all() -> None:
    """فهرست مدل‌های حساسی که تغییراتشان باید ثبت شود."""
    from catalog.models import Product, ProductDocument, ProductRelation
    from customers.models import Company
    from finance.models import Cheque, Invoice
    from inventory.models import PurchaseRequest, StockItem, StockMove
    from orders.models import Approval, Order, OrderLine
    from pricing.models import PriceList, PriceListItem, QuantityPriceBreak
    from quotes.models import Quote, QuoteLine

    track(Product, ("base_price", "min_order_qty", "max_order_qty", "packaging_multiple",
                    "availability", "is_active", "lead_time_days", "specs", "name"))
    track(ProductDocument, ("version", "is_latest", "title", "approved_by"))
    track(ProductRelation, ("kind", "target_id", "note"))
    track(PriceList, ("name", "valid_from", "valid_until", "is_active", "discount_pct"))
    track(PriceListItem, ("price", "valid_from", "valid_until"))
    track(QuantityPriceBreak, ("min_qty", "price", "discount_pct"))
    track(Company, ("name", "credit_limit", "payment_terms", "price_list_id", "sales_rep_id",
                    "kyc_status", "is_active"))
    track(StockItem, ("on_hand", "reserved", "incoming", "min_level", "reorder_point"))
    track(StockMove, ("qty", "kind", "unit_cost", "reference"))
    track(PurchaseRequest, ("status", "qty"))
    track(Quote, ("status", "assigned_to_id", "discount_pct", "valid_until", "sla_due_at",
                  "internal_note"))
    track(QuoteLine, ("qty", "offered_price", "discount_pct"))
    track(Order, ("status", "payment_method", "shipping_cost", "po_number", "waybill_number",
                  "internal_note", "expected_delivery_at"))
    track(OrderLine, ("qty", "unit_price", "discount_pct", "qty_reserved", "qty_shipped"))
    track(Approval, ("status", "approver_id", "comment"))
    track(Invoice, ("status", "moadian_status", "total", "due_date", "moadian_tax_id"))
    track(Cheque, ("status", "due_date", "amount", "bank"))
