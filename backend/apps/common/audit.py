"""ثبت رخدادهای مدل‌ها؛ منبع دادهٔ لاگ پنل پیشرفته."""
from __future__ import annotations

from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.db.models.fields.files import FieldFile

_request = ContextVar("audit_request", default=None)

# مدل‌های زیرساختی جنگو و هر دادهٔ حساس در لاگ ثبت نمی‌شوند.
TRACKED_APPS = {
    "accounts", "catalog", "inventory", "pricing", "carts", "orders",
    "company", "website", "content", "rfq", "notifications",
}
SENSITIVE_FIELD_NAMES = {"password", "code_hash", "token", "secret", "access_token", "refresh_token"}


def set_request(request):
    return _request.set(request)


def reset_request(token):
    _request.reset(token)


def should_track(sender) -> bool:
    return sender._meta.app_label in TRACKED_APPS


def _value(value):
    if isinstance(value, FieldFile):
        return value.name
    if isinstance(value, (datetime, date, Decimal, UUID)):
        return str(value)
    return value


def snapshot(instance) -> dict:
    data = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.name in SENSITIVE_FIELD_NAMES:
            continue
        data[field.name] = _value(getattr(instance, field.attname))
    return data


def _request_details():
    request = _request.get()
    if request is None:
        return None, "", "", None
    user = getattr(request, "user", None)
    actor = user if getattr(user, "is_authenticated", False) else None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    remote_addr = (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None
    return actor, request.method[:10], request.path[:500], remote_addr


def write_event(instance, action: str, changes: dict):
    # Import محلی از حلقهٔ import در زمان آماده‌شدن app جلوگیری می‌کند.
    from .models import AuditEvent

    actor, method, path, remote_addr = _request_details()
    AuditEvent.objects.create(
        actor=actor,
        action=action,
        app_label=instance._meta.app_label,
        model_name=instance._meta.model_name,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=changes,
        request_method=method,
        request_path=path,
        remote_addr=remote_addr,
    )
