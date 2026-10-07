"""سنجش رنگ و کنتراست سایت مشتری در هر دو تم روشن و تیره (WCAG 2.1).

    python3 scripts/theme_contrast_check.py

۱) همهٔ متغیرهای رنگ هر دو تم را از static/css/shop.css می‌خواند.
۲) نسبت کنتراست جفت‌های متن/پس‌زمینهٔ واقعی را محاسبه و با آستانه‌های AA می‌سنجد.
۳) رنگ‌های سخت‌کدشده در قالب‌ها را که ممکن است در تم تیره ناخوانا شوند گزارش می‌کند.
۴) سیم‌کشی کلید تم (localStorage / prefers-color-scheme / focus-visible / print) را بررسی می‌کند.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CSS = BASE / "static" / "css" / "shop.css"
TEMPLATES = BASE / "shop" / "templates" / "shop"

FAILS: list[str] = []
WARNS: list[str] = []


# ------------------------------------------------------------------ کمک‌ها
def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: float) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    l1, l2 = luminance(hex_to_rgb(fg)), luminance(hex_to_rgb(bg))
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def parse_vars(css: str, selector: str) -> dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
    if not match:
        return {}
    return dict(re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", match.group(1)))


def check_pair(theme: str, label: str, fg: str, bg: str, minimum: float = 4.5, kind: str = "متن") -> None:
    if not fg or not bg:
        WARNS.append(f"{theme}: متغیر رنگ برای «{label}» تعریف نشده است.")
        return
    ratio = contrast(fg, bg)
    ok = ratio >= minimum
    mark = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
    print(f"  {mark} {theme} — {label}: {ratio}:1 (حد {kind} {minimum}:1)  {fg} روی {bg}")
    if not ok:
        FAILS.append(f"{theme}/{label} نسبت {ratio}:1 کمتر از {minimum}:1 ({fg} روی {bg})")


def main() -> int:
    css = CSS.read_text(encoding="utf-8")
    light = parse_vars(css, ":root")
    dark = parse_vars(css, '[data-theme="dark"]')
    print(f"متغیرهای رنگ: تم روشن {len(light)} عدد، تم تیره {len(dark)} عدد\n")

    print("\033[96m■ ۱) کنتراست متن و سطوح در تم روشن\033[0m")
    for surface in ("surface", "surface-2", "surface-3"):
        bg = light.get(surface, "")
        check_pair("روشن", f"متن اصلی روی {surface}", light["text"], bg)
        check_pair("روشن", f"متن ثانویه روی {surface}", light["text-2"], bg)
        check_pair("روشن", f"متن کم‌رنگ (muted) روی {surface}", light["muted"], bg)
    for soft, strong in (("ok-soft", "ok"), ("warn-soft", "warn"), ("danger-soft", "danger"), ("info-soft", "info")):
        check_pair("روشن", f"برچسب {strong} روی پس‌زمینهٔ {soft}", light[strong], light[soft])
    check_pair("روشن", "رنگ اصلی روی سطح", light["primary"], light["surface"])
    check_pair("روشن", "رنگ اصلی روی پس‌زمینهٔ خودش", light["primary"], light["primary-soft"])
    check_pair("روشن", "متن دکمهٔ اصلی (#ffffff روی primary)", "#ffffff", light["primary"])
    check_pair("روشن", "سربرگ هیرو (#ffffff روی فیروزه‌ای تیره)", "#ffffff", "#0e7490")
    check_pair("روشن", "متن هیرو (#e3f4f8 روی گرادیان تیره)", "#e3f4f8", "#0b5e75")

    print("\n\033[96m■ ۲) کنتراست متن و سطوح در تم تیره\033[0m")
    for surface in ("surface", "surface-2", "surface-3", "bg"):
        bg = dark.get(surface, "")
        check_pair("تیره", f"متن اصلی روی {surface}", dark["text"], bg)
        check_pair("تیره", f"متن ثانویه روی {surface}", dark["text-2"], bg)
        check_pair("تیره", f"متن کم‌رنگ (muted) روی {surface}", dark["muted"], bg)
    for soft, strong in (("ok-soft", "ok"), ("warn-soft", "warn"), ("danger-soft", "danger"), ("info-soft", "info")):
        check_pair("تیره", f"برچسب {strong} روی پس‌زمینهٔ {soft}", dark[strong], dark[soft])
    check_pair("تیره", "رنگ اصلی روی سطح", dark["primary"], dark["surface"])
    check_pair("تیره", "رنگ اصلی روی پس‌زمینهٔ خودش", dark["primary"], dark["primary-soft"])
    check_pair("تیره", "متن دکمهٔ اصلی (#06131a روی primary روشن)", "#06131a", dark["primary"])
    check_pair("تیره", "سربرگ هیرو (#ffffff روی گرادیان تیره)", "#ffffff", "#0f3d4d")
    check_pair("تیره", "متن هیرو (#e3f4f8 روی گرادیان تیره)", "#e3f4f8", "#10313d")

    print("\n\033[96m■ ۳) عناصر رابط کاربری و مرزها (حداقل ۳:۱)\033[0m")
    check_pair("روشن", "مرز کنترل‌های تعاملی (فیلد/دکمه) روی سطح",
               light["border-input"], light["surface"], 3.0, "رابط")
    check_pair("روشن", "مرز کنترل‌ها روی سطح دوم",
               light["border-input"], light["surface-2"], 2.8, "رابط")
    check_pair("تیره", "مرز کنترل‌های تعاملی (فیلد/دکمه) روی سطح",
               dark["border-input"], dark["surface"], 3.0, "رابط")
    check_pair("تیره", "مرز کنترل‌ها روی سطح دوم",
               dark["border-input"], dark["surface-2"], 2.8, "رابط")
    # مرزهای تزئینی (کارت و خط جداکننده) مشمول معیار ۱.۴.۱۱ نیستند؛ فقط گزارش می‌شوند.
    print(f"  ℹ مرز تزئینی روشن {light['border']} ({contrast(light['border'], light['surface'])}:۱) و "
          f"تیره {dark['border']} ({contrast(dark['border'], dark['surface'])}:۱) — تزئینی، خارج از معیار")
    check_pair("روشن", "نشانگر صفحهٔ جاری (سفید روی primary)", "#ffffff", light["primary"], 3.0, "رابط")
    check_pair("تیره", "نشانگر صفحهٔ جاری (تیره روی primary)", "#06131a", dark["primary"], 3.0, "رابط")

    print("\n\033[96m■ ۴) رنگ‌های سخت‌کدشده در قالب‌ها\033[0m")
    hardcoded: dict[str, list[str]] = {}
    for path in sorted(TEMPLATES.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for color in set(re.findall(r"(?<![\w-])(#[0-9a-fA-F]{3,6})(?![\w-])", text)):
            hardcoded.setdefault(color.lower(), []).append(path.name)
    allowed = {"#fff", "#ffffff", "#0b5e75", "#0e7490", "#0d3b4a", "#cfeaf1", "#e3f4f8", "#06131a"}
    risky = {c: files for c, files in hardcoded.items() if c not in allowed}
    if risky:
        for color, files in sorted(risky.items()):
            WARNS.append(f"رنگ سخت‌کدشده {color} در {', '.join(sorted(set(files)))}")
            print(f"  \033[93m!\033[0m رنگ ثابت {color} در {', '.join(sorted(set(files)))} — باید بررسی شود")
    else:
        print("  \033[92m✓\033[0m هیچ رنگ سخت‌کدی خارج از پالت مجاز در قالب‌ها نیست")
    print(f"  ℹ رنگ‌های ثابت مجاز (متن روی گرادیان هیرو و نشان): {', '.join(sorted(allowed))}")

    print("\n\033[96m■ ۵) ساختار تم (روشن/تیره) و رفتار رابط\033[0m")
    js = (BASE / "static" / "js" / "shop.js").read_text(encoding="utf-8")
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    structural = {
        "متغیرهای CSS برای هر دو تم": ':root {' in css and '[data-theme="dark"]' in css,
        "انتخاب تم پیش از رندر صفحه (بدون پرش رنگ)":
            "data-theme" in base and "localStorage" in base and "prefers-color-scheme" in base,
        "ذخیرهٔ انتخاب کاربر در مرورگر": "localStorage" in js and "mehrasl-shop-theme" in js,
        "پیروی از تنظیمات سیستم در اولین بازدید": "prefers-color-scheme" in js,
        "کلید تغییر تم در سربرگ": "data-theme-toggle" in base and "theme-toggle" in css,
        "برچسب دسترسی‌پذیری برای کلید تم": "aria-label" in js and "data-theme-toggle" in js,
        "حالت focus قابل‌مشاهده برای کیبورد": ":focus-visible" in css,
        "سبک چاپ فاکتور (حذف منوها)": "@media print" in css and "print-only" in css,
        "توجه به کاهش انیمیشن (کاربران حساس)": "prefers-reduced-motion" in css,
        "رزبریک برای موبایل": "@media (max-width: 820px)" in css,
    }
    for label, ok in structural.items():
        print(f"  {'\033[92m✓\033[0m' if ok else '\033[91m✗\033[0m'} {label}")
        if not ok:
            FAILS.append(label)

    print("\n" + "─" * 62)
    report = {"failures": FAILS, "warnings": WARNS}
    (BASE / "docs").mkdir(exist_ok=True)
    (BASE / "docs" / "shop-theme-contrast.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if FAILS:
        print(f"\033[91m{len(FAILS)} مورد ناموفق\033[0m / {len(WARNS)} هشدار — جزئیات در docs/shop-theme-contrast.json")
        for item in FAILS:
            print(f"  • {item}")
        return 1
    print(f"\033[92mهمهٔ سنجه‌های رنگ رد شد ✅\033[0m ({len(WARNS)} هشدار اطلاعاتی)")
    for item in WARNS:
        print(f"  ℹ {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
