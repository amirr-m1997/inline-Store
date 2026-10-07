"""سنجش UX/UI پنل: اندازه‌گیری خودکار معیارهای رابط کاربری روی همه‌ی صفحه‌های ادمین.

اجرا:
    python3 scripts/ux_audit.py            # گزارش متنی در ترمینال
    python3 scripts/ux_audit.py --json     # خروجی JSON برای پردازش بیشتر
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib import admin as dj_admin  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

CUSTOM_PAGES = {
    "داشبورد": "/admin/",
    "گزارش‌ساز": "/admin/reports/",
    "سفارش سریع": "/admin/quick-order/",
    "اعلان‌ها": "/admin/alerts/",
    "ورود": "/admin/login/",
}


def client(logged_in: bool = True):
    """کلاینت تست؛ برای صفحه‌ی ورود، کلاینت ناشناس لازم است (وگرنه ریدایرکت می‌شود)."""
    c = Client()
    if logged_in:
        user = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
        c.force_login(user)
    return c


# ------------------------------------------------------------------ سنجه‌ها
def audit_page(html: str) -> dict:
    """معیارهای UI یک صفحه‌ی ادمین."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)

    headers = re.findall(r"<th\b[^>]*class=\"([^\"]*)\"", body)
    column_headers = [h for h in headers if "column-" in h or "action-checkbox" in h]

    # عرض تقریبی جدول: هر ستون ~۱۳۰ پیکسل؛ آستانه‌ی هشدار برای صفحه‌ی ۱۳۶۶px
    estimated_width = len(column_headers) * 130

    scroll_wrappers = len(re.findall(r"overflow-x-auto|overflow-x: auto|panel-scroll", body))
    table_count = len(re.findall(r"<table\b", body))
    th_scope = len(re.findall(r"<th[^>]*scope=", body))

    latin_runs = re.findall(r">([A-Za-z][A-Za-z0-9\-./_@ ]{4,40})<", body)
    nums_western = len(re.findall(r">\s*\d[\d,\.]{2,}\s*<", body))

    empty_states = len(re.findall(r"panel-empty|no results|No data|نتیجه‌ای یافت نشد|داده‌ای موجود نیست", body))
    has_search_box = bool(re.search(r'name="q"', body))
    labels = len(re.findall(r"<label\b", body))
    inputs = len(re.findall(r"<input\b(?![^>]*type=\"hidden\")", body))
    selects = len(re.findall(r"<select\b", body))
    buttons = len(re.findall(r"<button\b|<a class=\"panel-btn", body))

    return {
        "columns": column_headers,
        "column_count": len(column_headers),
        "estimated_table_width_px": estimated_width,
        "scroll_wrappers": scroll_wrappers,
        "tables": table_count,
        "th_with_scope": th_scope,
        "latin_runs": len(latin_runs),
        "western_number_cells": nums_western,
        "empty_states": empty_states,
        "has_search_box": has_search_box,
        "empty_search_state": None,   # پر می‌شود با درخواست بی‌نتیجه
        "labels": labels,
        "inputs": inputs,
        "selects": selects,
        "buttons": buttons,
        "has_h1": bool(re.search(r"<h1\b", body)),
        "has_breadcrumb": bool(re.search(r"breadcrumb", body, re.I)),
        "has_rtl": 'dir="rtl"' in html,
        "has_persian": bool(re.search(r"[\u0600-\u06FF]", body)),
    }


def run(json_out: bool = False) -> None:
    c = client()
    report: dict = {"custom_pages": {}, "changelists": {}, "css": {}, "summary": {}}

    anonymous = client(logged_in=False)
    for name, url in CUSTOM_PAGES.items():
        # صفحه‌ی ورود فقط با کلاینت ناشناس معنادار است
        source = anonymous if name == "ورود" else c
        html = source.get(url).content.decode()
        report["custom_pages"][name] = audit_page(html) | {"bytes": len(html)}

    widest = []
    for model in dj_admin.site._registry:
        meta = model._meta
        base = f"/admin/{meta.app_label}/{meta.model_name}/"
        html = c.get(base).content.decode()
        data = audit_page(html) | {"label": str(meta.verbose_name_plural)}
        if data["has_search_box"]:
            # حالت خالی واقعی: جست‌وجوی بی‌نتیجه
            empty_html = c.get(base + "?q=zzzz_audit_no_match").content.decode()
            empty_body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", empty_html, flags=re.S)
            data["empty_search_state"] = bool(
                re.search(r"نتیجه‌ای یافت نشد|No results|no results", empty_body)
            )
        report["changelists"][f"{meta.app_label}.{meta.model_name}"] = data
        widest.append([data["estimated_table_width_px"], data["column_count"],
                       f"{meta.app_label}.{meta.model_name}", data["scroll_wrappers"]])

    css = (ROOT / "static/css/panel.css").read_text(encoding="utf-8")
    report["css"] = {
        "font_sizes": sorted({float(x) for x in re.findall(r"font-size:\s*([\d.]+)px", css)}),
        "colors": sorted(set(re.findall(r"#[0-9a-fA-F]{6}", css))),
        "has_focus_style": ":focus" in css or "focus-visible" in css,
        "has_overflow_rule": "overflow-x" in css,
        "has_dark_mode": ".dark" in css or "prefers-color-scheme" in css,
        "has_print_style": "@media print" in css,
        "breakpoints": sorted({int(x) for x in re.findall(r"max-width:\s*(\d+)px", css)}),
        "bidi_isolation": "unicode-bidi" in css or "bdi" in css,
        "lines": len(css.splitlines()),
    }

    report["summary"] = {
        "changelists": len(report["changelists"]),
        "widest_tables": sorted(widest, key=lambda row: -row[0])[:8],
        "pages_without_empty_state": [
            key for key, data in report["changelists"].items() if data["empty_states"] == 0
        ],
        "pages_with_working_empty_search": [
            key for key, data in report["changelists"].items() if data.get("empty_search_state")
        ],
        "searched": [key for key, data in report["changelists"].items() if data["has_search_box"]],
        "pages_without_search": [
            key for key, data in report["changelists"].items() if data["inputs"] == 0 and data["selects"] == 0
        ],
    }

    if json_out:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return

    print("=" * 76)
    print("۱) صفحه‌های سفارشی")
    for name, data in report["custom_pages"].items():
        print(f"  {name:12} ستون‌ها:{data['column_count']:2} | جدول:{data['tables']} | "
              f"h1:{'✓' if data['has_h1'] else '✗'} | بریدکرامب:{'✓' if data['has_breadcrumb'] else '✗'} | "
              f"حالت خالی:{data['empty_states']} | RTL:{'✓' if data['has_rtl'] else '✗'}")
    print("\n۲) پهن‌ترین جدول‌ها (تخمین عرض = تعداد ستون × ۱۳۰px)")
    for width, cols, name, scroll in report["summary"]["widest_tables"]:
        flag = "⚠ سرریز" if width > 1100 and scroll == 0 else "✓"
        print(f"  {flag} {name:26} {cols:2} ستون ≈ {width:5}px | ناحیه اسکرول:{scroll}")
    print("\n۳) CSS پنل")
    for key, value in report["css"].items():
        print(f"  {key:20} {value}")
    print("\n۴) جمع‌بندی")
    print(f"  چک‌لیست‌های بررسی‌شده: {report['summary']['changelists']}")
    # توجه: سنجه‌ی نشانه‌محور «بدون حالت خالی» مثبت کاذب می‌دهد؛ سنجه‌ی معتبر خط بعدی است.
    total = len(report['summary']['searched'])
    ok = len(report['summary']['pages_with_working_empty_search'])
    print(f"  حالت خالی واقعی (جست‌وجوی بی‌نتیجه): {ok} از {total} فهرست دارای جست‌وجو")
    print(f"  بدون جست‌وجو/فیلتر: {report['summary']['pages_without_search'] or 'هیچ'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    run(parser.parse_args().json)
