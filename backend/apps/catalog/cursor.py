import hashlib
import json
from datetime import date, datetime
from decimal import Decimal

from django.core import signing
from django.core.exceptions import ValidationError
from django.db.models import Q


def _context(params):
    values = []
    for key in sorted(params.keys()):
        if key in {"cursor", "page"}:
            continue
        values.append((key, list(params.getlist(key))))
    raw = json.dumps(values, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _pack(value):
    if isinstance(value, datetime): return {"type": "datetime", "value": value.isoformat()}
    if isinstance(value, date): return {"type": "date", "value": value.isoformat()}
    if isinstance(value, Decimal): return {"type": "decimal", "value": str(value)}
    if isinstance(value, bool): return {"type": "bool", "value": value}
    if isinstance(value, int): return {"type": "int", "value": value}
    if isinstance(value, float): return {"type": "float", "value": value}
    return {"type": "string", "value": "" if value is None else str(value)}


def _unpack(value):
    kind, raw = value.get("type"), value.get("value")
    if kind == "datetime": return datetime.fromisoformat(raw)
    if kind == "date": return date.fromisoformat(raw)
    if kind == "decimal": return Decimal(raw)
    if kind == "int": return int(raw)
    if kind == "float": return float(raw)
    if kind == "bool": return bool(raw)
    return raw


def encode_cursor(params, ordering, row):
    fields = [{"field": field, "descending": descending, "value": _pack(getattr(row, field))} for field, descending in ordering]
    payload = {"version": 1, "context": _context(params), "ordering": [[field, descending] for field, descending in ordering], "fields": fields}
    return signing.dumps(payload, salt="catalog-query-cursor")


def decode_cursor(token, params, ordering):
    try:
        payload = signing.loads(token, salt="catalog-query-cursor")
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        raise ValidationError({"cursor": "نشانگر صفحه‌بندی معتبر نیست."})
    expected_ordering = [[field, descending] for field, descending in ordering]
    if payload.get("version") != 1 or payload.get("context") != _context(params) or payload.get("ordering") != expected_ordering:
        raise ValidationError({"cursor": "نشانگر صفحه‌بندی با جست‌وجو یا مرتب‌سازی فعلی سازگار نیست."})
    try:
        return [(item["field"], bool(item["descending"]), _unpack(item["value"])) for item in payload["fields"]]
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValidationError({"cursor": "نشانگر صفحه‌بندی خراب است."})


def apply_keyset(queryset, cursor_fields):
    disjunction = Q()
    equal_prefix = Q()
    for field, descending, value in cursor_fields:
        operator = "lt" if descending else "gt"
        disjunction |= equal_prefix & Q(**{f"{field}__{operator}": value})
        equal_prefix &= Q(**{field: value})
    return queryset.filter(disjunction)
