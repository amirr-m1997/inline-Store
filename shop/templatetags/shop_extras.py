"""فیلترهای کمکی قالب‌های سایت مشتری."""
from __future__ import annotations

from django import template

from core.utils import num

register = template.Library()

BADGE_BY_STATUS = {
    "ok": "badge-ok",
    "warn": "badge-warn",
    "danger": "badge-danger",
    "info": "badge-info",
}


@register.filter
def get_item(mapping, key):
    """خواندن مقدار از دیکشنری با کلید (برای جدول قیمت هر کالا در فهرست)."""
    try:
        return mapping.get(key) or mapping.get(str(key))
    except AttributeError:
        return None


@register.filter
def badge_class(key):
    return BADGE_BY_STATUS.get(str(key), "badge")


@register.filter
def qty_fa(value):
    """تعداد: عدد صحیح بدون اعشار، اعشاری با دو رقم."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    return num(number, 0) if abs(number - round(number)) < 0.001 else num(number, 2)


@register.filter
def latin(value):
    """عدد با ارقام لاتین برای استفاده در value فیلدهای HTML (input[type=number])."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    text = f"{number:.2f}".rstrip("0").rstrip(".")
    return text or "0"


@register.filter
def status_tone(status: str) -> str:
    """رنگ برچسب بر پایهٔ وضعیت سفارش/فاکتور."""
    text = str(status)
    if text in ("تحویل شده", "تسویه شده", "تأیید شده", "ارسال شده", "موجود (نو)", "آماده تحویل"):
        return "badge-ok"
    if text in ("لغو شده", "رد شده", "متوقف تولید", "ناموجود", "معوق"):
        return "badge-danger"
    if text in ("در انتظار تأیید", "در حال آماده‌سازی", "کمبود موجودی", "ساخت به سفارش", "نیازمند استعلام"):
        return "badge-warn"
    return "badge-info"
