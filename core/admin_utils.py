"""ابزارهای مشترک رابط ادمین: بج رنگی، مبلغ، تاریخ شمسی."""
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .utils import fa, jalali, jalali_dt, money_short, num

COLORS = {
    "ok": "#12855f",
    "warn": "#b45309",
    "danger": "#c02626",
    "info": "#1d4ed8",
    "violet": "#6d28d9",
    "primary": "#0e7490",
    "muted": "#64748b",
}


def badge(text, color: str | None = None, key: str = "muted"):
    """نمایش یک برچسب رنگی (badge) در لیست‌های ادمین."""
    color = color or COLORS.get(key, COLORS["muted"])
    return format_html(
        '<span style="background:{}1a;color:{};padding:2px 8px;border-radius:999px;'
        'font-size:11px;font-weight:600;white-space:nowrap">{}</span>',
        color, color, text,
    )


def status_badge(text, key: str = "muted"):
    return badge(text, key=key)


def money(value, suffix: str = "تومان"):
    """نمایش مبلغ با جداکننده و ارقام فارسی."""
    return format_html(
        '<span style="font-variant-numeric:tabular-nums;white-space:nowrap">{}</span>',
        f"{num(value, 0)} {suffix}" if value else "—",
    )


def money_compact(value):
    return format_html(
        '<span style="font-variant-numeric:tabular-nums;white-space:nowrap">{}</span>',
        money_short(value) if value else "—",
    )


def progress_bar(pct: int, color: str | None = None):
    """نوار پیشرفت افقی برای مصرف اعتبار یا سهم فروش."""
    pct = max(min(int(pct or 0), 100), 0)
    color = color or COLORS["primary"]
    return format_html(
        '<div style="display:flex;align-items:center;gap:8px">'
        '<div style="flex:1;min-width:70px;height:7px;background:#eef2f8;border-radius:6px;overflow:hidden">'
        '<div style="width:{}%;height:100%;background:{}"></div></div>'
        '<span style="font-size:11px;color:#64748b">{}</span></div>',
        pct, color, fa(f"{pct}٪"),
    )


def diff_cell(old, new, fmt=str):
    """نمایش «قبل ← بعد» با رنگ."""
    return format_html(
        '<span style="font-variant-numeric:tabular-nums">'
        '<span style="color:#c02626;text-decoration:line-through;opacity:.75">{}</span>'
        ' <span style="color:#64748b">←</span> '
        '<b style="color:#12855f">{}</b></span>',
        fmt(old) if old not in (None, "") else "—", fmt(new) if new not in (None, "") else "—",
    )


def jalali_col(description: str):
    """دکوراتور اختصاصی برای نمایش تاریخ شمسی در list_display."""

    def decorator(func):
        def wrapper(self, obj):
            value = func(self, obj)
            return format_html('<span style="font-variant-numeric:tabular-nums">{}</span>',
                               jalali(value) if not hasattr(value, "hour") else jalali_dt(value))

        wrapper.short_description = description
        wrapper.admin_order_field = None
        return wrapper

    return decorator


def html_table(headers: list[str], rows: list[list], title: str = "") -> str:
    """ساخت جدول HTML کوچک برای فیلدهای readonly."""
    head = "".join(
        f'<th style="padding:6px 10px;text-align:right;font-size:11px;color:#64748b;'
        f'border-bottom:1px solid #e6eaf2;font-weight:600">{h}</th>' for h in headers
    )
    body = ""
    for row in rows:
        cells = "".join(
            f'<td style="padding:6px 10px;font-size:12px;border-bottom:1px solid #eef2f8">{c}</td>'
            for c in row
        )
        body += f"<tr>{cells}</tr>"
    title_html = f'<div style="margin-bottom:6px;font-weight:600">{title}</div>' if title else ""
    return format_html(
        '{}<table style="width:100%;border-collapse:collapse;background:#fff;border-radius:10px;'
        'overflow:hidden"><thead><tr>{}</tr></thead><tbody>{}</tbody></table>',
        title_html, format_html(head), format_html(body),
    )


class ModelHelpMixin:
    """کارت «این بخش چیست؟» را بالای فهرست و فرم افزودن/ویرایش هر مدل نشان می‌دهد.

    متن هر مدل از `core.model_docs.MODEL_HELP` خوانده می‌شود؛ روی قالب
    `admin/partials/model_help.html` رندر می‌شود (قابلیت خود unfold).
    """

    list_before_template = "admin/partials/model_help.html"
    change_form_before_template = "admin/partials/model_help.html"


class PanelModelAdmin(ModelHelpMixin, admin.ModelAdmin):
    """کلاس پایه‌ی ادمین پنل با تنظیمات مشترک."""

    list_per_page = 30
    save_on_top = True
    show_facets = admin.ShowFacets.ALWAYS if hasattr(admin, "ShowFacets") else True
    empty_value_display = "—"
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_fullwidth = True
