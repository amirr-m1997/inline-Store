"""خروجی Markdown از نام‌ها و توضیحات مدل‌های پنل.

اجرا:
    cd /home/user/mehrasl-panel
    python3 scripts/export_model_docs.py           # → docs/model-names-and-help.md
"""
from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.apps import apps as django_apps  # noqa: E402
from django.contrib import admin  # noqa: E402

from core.model_docs import MODEL_HELP, PAGE_HELP  # noqa: E402


def main() -> None:
    rows = []
    for model in sorted(admin.site._registry, key=lambda m: (m._meta.app_label, m._meta.model_name)):
        meta = model._meta
        key = f"{meta.app_label}.{meta.model_name}"
        rows.append((
            key,
            str(django_apps.get_app_config(meta.app_label).verbose_name),
            meta.verbose_name,
            meta.verbose_name_plural,
            MODEL_HELP.get(key, "—"),
        ))

    missing = [key for key, *_ in rows if MODEL_HELP.get(key) in (None, "—")]

    lines = [
        "# نام‌ها و توضیحات مدل‌های پنل ادمین مهراصل",
        "",
        "این فایل از `core/model_docs.py` و متادیتای مدل‌ها ساخته می‌شود (قابل تولید مجدد با "
        "`python3 scripts/export_model_docs.py`).",
        "",
        f"تعداد مدل‌های ثبت‌شده در پنل: **{len(rows)}** — مدل بدون توضیح: **{len(missing)}**",
        "",
        "| مدل (فنی) | اپ (فارسی) | نام مفرد | نام جمع | توضیح نمایش‌داده‌شده در پنل |",
        "|---|---|---|---|---|",
    ]
    for key, app_name, name, plural, help_text in rows:
        lines.append(f"| `{key}` | {app_name} | {name} | {plural} | {help_text} |")

    lines += [
        "",
        "## صفحه‌های سفارشی (بدون مدل)",
        "",
        "| نشانی | توضیح |",
        "|---|---|",
    ]
    for path, text in PAGE_HELP.items():
        lines.append(f"| `{path}` | {text} |")
    lines.append("")

    out = ROOT / "docs" / "model-names-and-help.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"نوشته شد: {out} ({len(rows)} مدل، {len(PAGE_HELP)} صفحه‌ی سفارشی)")


if __name__ == "__main__":
    main()
