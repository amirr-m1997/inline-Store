"""ابزارهای مشترک رابط ادمین: بج رنگی، مبلغ، تاریخ شمسی."""
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .palette import ACCENT, DANGER, INFO, MUTED, OK, VIOLET, WARN
from .utils import fa, jalali, jalali_dt, money_short, num

COLORS = {
    "ok": OK,
    "warn": WARN,
    "danger": DANGER,
    "info": INFO,
    "violet": VIOLET,
    "primary": ACCENT,
    "muted": MUTED,
}


def badge(text, color: str | None = None, key: str = "muted"):
    """نمایش یک برچسب رنگی (badge) در لیست‌های ادمین."""
    color = color or COLORS.get(key, COLORS["muted"])
    return format_html('<span class="panel-badge" style="--badge:{}">{}</span>', color, text)


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
        '<div class="panel-progress">'
        '<div class="panel-progress-track">'
        '<div class="panel-progress-fill" style="width:{}%;--fill:{}"></div></div>'
        '<span class="panel-progress-label">{}</span></div>',
        pct, color, fa(f"{pct}٪"),
    )


def diff_cell(old, new, fmt=str):
    """نمایش «قبل ← بعد» با رنگ."""
    return format_html(
        '<span class="panel-diff">'
        '<span class="panel-diff-old">{}</span>'
        ' <span class="panel-diff-arrow">←</span> '
        '<b class="panel-diff-new">{}</b></span>',
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
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{c}</td>" for c in row)
        body += f"<tr>{cells}</tr>"
    title_html = f'<div class="panel-inline-table__title">{title}</div>' if title else ""
    return format_html(
        '{}<div class="panel-inline-table"><table><thead><tr>{}</tr></thead>'
        '<tbody>{}</tbody></table></div>',
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
    # با True، جنگو هر FK موجود در list_display را خودش با select_related
    # همراه میکند (جلوگیری از کوئری N+1 در فهرستهای پنل).
    list_select_related = True
    save_on_top = True
    show_facets = admin.ShowFacets.ALWAYS if hasattr(admin, "ShowFacets") else True
    empty_value_display = "—"
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_fullwidth = True
