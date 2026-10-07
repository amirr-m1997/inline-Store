"""فیلترها و تگ‌های کمکی قالب‌های پنل."""
from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

from core.palette import ACCENT, DANGER, INFO, MUTED, OK, VIOLET, WARN
from core.utils import fa, jalali, jalali_dt, money, money_short, num

register = template.Library()


@register.filter
def fa_digits(value):
    return fa(value)


@register.filter
def money_fa(value, decimals=0):
    return money(value, int(decimals))


@register.filter
def money_s(value):
    return money_short(value)


@register.filter
def num_fa(value, decimals=0):
    return num(value, int(decimals))


@register.filter
def jdate(value):
    return jalali(value)


@register.filter
def jdatetime_fa(value):
    return jalali_dt(value)


@register.filter
def pct(value, decimals=0):
    try:
        return fa(f"{round(float(value), int(decimals))}٪")
    except (TypeError, ValueError):
        return "—"


@register.filter
def pct_unfilled(value, decimals=0):
    """درصد بدون علامت درصد (برای نوار پیشرفت)."""
    try:
        return fa(round(float(value), int(decimals)))
    except (TypeError, ValueError):
        return 0


@register.simple_tag
def kpi_icon(name):
    icons = {
        "sales": "trending_up", "rfq": "forum", "approval": "approval", "stock": "inventory_2",
        "credit": "account_balance_wallet", "money": "payments", "chart": "bar_chart",
    }
    return icons.get(name, "insights")


@register.filter
def label_for(value, choices):
    """تبدیل کلید به عنوان فارسی از فهرست choices."""
    for key, label in choices:
        if str(key) == str(value):
            return label
    return value


BADGE_COLORS = {
    "ok": OK, "success": OK, "warn": WARN, "warning": WARN,
    "danger": DANGER, "error": DANGER, "info": INFO, "violet": VIOLET,
    "primary": ACCENT, "muted": MUTED,
}


@register.simple_tag
def badge(text, color="muted"):
    """برچسب رنگی؛ هم رنگ هگز و هم کلید واژگانی (ok/warn/danger/info/…) را می‌پذیرد.

    رنگ به‌صورت متغیر CSS به کلاس `.panel-badge` داده می‌شود؛ در تم تیره
    خودِ CSS آن را روشن می‌کند تا کنتراست متن ≥ ۴٫۵:۱ بماند.
    """
    color = BADGE_COLORS.get(str(color).lower(), color)
    return mark_safe(f'<span class="panel-badge" style="--badge:{color}">{text}</span>')


@register.inclusion_tag("core/partials/kpi_card.html")
def kpi_card(title, value, hint="", delta=None, icon="sales", spark="", trend=0):
    return {"title": title, "value": value, "hint": hint, "delta": delta,
            "icon": icon, "spark": spark, "trend": trend}


@register.simple_tag
def model_help(app_label: str, model_name: str) -> str:
    """توضیح فارسی مدل برای کارت «این بخش چیست؟» در پنل ادمین."""
    from core.model_docs import help_for

    return help_for(app_label or "", model_name or "")
