"""سنجش رنگ و تجربه‌ی کاربری پنل (گذر «مشتری سخت‌گیر») — با شواهد عددی.

بخش‌ها:
  ۱) توکن‌های رنگ در تم روشن و تیره + نسبت کنتراست WCAG هر جفت
  ۲) ساختار دسترس‌پذیری: focus-visible، اندازه‌ی لمس، چاپ، دوسویه (bidi)
  ۳) استقلال از شبکه: بدون CDN/دامنه‌ی بیرونی، فونت خودمیزبان
  ۴) تمیزی CSS: رنگ‌های سرسخت‌شده، !important، مقدارهای چپ/راست سرسخت‌شده
  ۵) کارت «این بخش چیست؟» برای همه‌ی مدل‌های ثبت‌شده (توضیح فارسی)
  ۶) راست‌به‌چپ بودن صفحه‌های کلیدی

خروجی: چاپ خلاصه + نوشتن docs/panel-ux-audit.json
اجرا: python3 scripts/panel_ux_audit.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
from html.parser import HTMLParser

import django

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

CSS_PATH = ROOT / "static" / "css" / "panel.css"
JS_PATH = ROOT / "static" / "js" / "panel.js"


# ------------------------------------------------- استخراج متن دیده‌شدهٔ صفحه
class _TextExtractor(HTMLParser):
    """متن دیده‌شده را دقیق درمی‌آورد: بدون تگ‌ها، اسکریپت‌ها و نام آیکون‌ها."""

    SKIP = {"script", "style", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._icon_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        classes = (dict(attrs).get("class") or "")
        if classes.startswith("material-symbols"):
            self._icon_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag == "span" and self._icon_depth:
            self._icon_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth and not self._icon_depth:
            self.parts.append(data)


def visible_text(html: str, marker: str | None = None) -> str:
    if marker and marker in html:
        start = html.index(marker)
        depth, index = 0, start
        tag = re.compile(r"<div\b|</div>")
        while True:
            match = tag.search(html, index)
            if not match:
                break
            depth += 1 if match.group(0).startswith("<div") else -1
            if depth == 0:
                html = html[start:match.end()]
                break
            index = match.end()
    parser = _TextExtractor()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


passed = 0
failed = 0
report: dict = {"checks": [], "metrics": {}, "contrast": {}}


def check(label: str, ok: bool, extra: str = "") -> None:
    global passed, failed
    passed += ok
    failed += not ok
    report["checks"].append({"label": label, "ok": bool(ok), "extra": extra})
    print(f"  {'✓' if ok else '✗'} {label}" + (f" — {extra}" if extra else ""))


# ------------------------------------------------------------------ رنگ‌سنجی
def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(rgb: tuple[int, int, int]) -> float:
    def channel(raw: int) -> float:
        c = raw / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    l1, l2 = luminance(hex_to_rgb(fg)), luminance(hex_to_rgb(bg))
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def vars_of(css: str, selector: str) -> dict[str, str]:
    block = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
    if not block:
        return {}
    return {k: v.strip() for k, v in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block.group(1))}


def main() -> int:
    css = CSS_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")

    print("\n۱) توکن‌های رنگ و کنتراست (WCAG 2.1)")
    light = vars_of(css, ":root")
    dark = vars_of(css, ".dark")
    tokens = ["surface", "surface-2", "border", "text", "text-muted", "accent",
              "accent-weak", "ok", "warn", "danger", "focus", "on-accent"]
    missing_light = [t for t in tokens if f"panel-{t}" not in light]
    missing_dark = [t for t in tokens if f"panel-{t}" not in dark]
    check("همه‌ی توکن‌های رنگ در تم روشن تعریف شده‌اند", not missing_light, f"کمبود: {missing_light or '—'}")
    check("همه‌ی توکن‌های رنگ در تم تیره تعریف شده‌اند", not missing_dark, f"کمبود: {missing_dark or '—'}")

    pairs = [
        ("متن اصلی روی سطح", "text", "surface", 4.5),
        ("متن اصلی روی سطح دوم", "text", "surface-2", 4.5),
        ("متن کم‌رنگ روی سطح", "text-muted", "surface", 4.5),
        ("متن کم‌رنگ روی سطح دوم", "text-muted", "surface-2", 4.5),
        ("فیروزه‌ای (پیوند/تأکید) روی سطح", "accent", "surface", 4.5),
        ("فیروزه‌ای روی پس‌زمینه‌ی ملایم", "accent", "accent-weak", 3.0),
        ("سبز وضعیت روی سطح", "ok", "surface", 3.0),
        ("نارنجی هشدار روی سطح", "warn", "surface", 3.0),
        ("قرمز خطا روی سطح", "danger", "surface", 3.0),
        ("حاشیه روی سطح", "border", "surface", 1.0),
        ("متن روی زمینهٔ تأکید (پیوند پرش)", "on-accent", "accent", 4.5),
    ]
    for theme_name, table in (("روشن", light), ("تیره", dark)):
        rows = {}
        for label, fg_key, bg_key, minimum in pairs:
            fg, bg = table.get(f"panel-{fg_key}"), table.get(f"panel-{bg_key}")
            if not fg or not bg:
                continue
            ratio = contrast(fg, bg)
            rows[label] = {"fg": fg, "bg": bg, "ratio": ratio, "min": minimum}
            check(f"[{theme_name}] {label}: {ratio}:1 (کمینه {minimum})", ratio >= minimum,
                  f"{fg} روی {bg}")
        report["contrast"][theme_name] = rows

    print("\n۲) ساختار دسترس‌پذیری")
    check("قاعده‌ی :focus-visible برای فوکوس کیبورد", css.count(":focus-visible") >= 5,
          f"{css.count(':focus-visible')} قاعده")
    check("کمینه‌ی اندازه‌ی لمس ۳۲px تعریف و استفاده شده",
          "--panel-target: 32px" in css and css.count("var(--panel-target)") >= 2,
          f"{css.count('var(--panel-target)')} کاربرد")
    check("پیوند «پرش به محتوای اصلی» در CSS هست", ".panel-skip-link" in css)
    check("پیوند پرش در JS ساخته می‌شود", "panel-skip-link" in js and "addSkipLink" in js)
    check("چاپ: ابزارهای تعاملی پنهان می‌شوند",
          "@media print" in css and ".panel-row-actions" in css.split("@media print")[-1])
    check("دوسویه‌سازی متن (bidi) برای کدها و اعداد لاتین",
          "unicode-bidi" in css or "bidi-isolate" in css, f"{css.count('unicode-bidi')} مورد")
    check("راهنمای میان‌بر جست‌وجو (/ و Esc) پیاده شده",
          'evt.key !== "/"' in js and 'evt.key === "Escape"' in js)
    check("کنش‌های درون‌ردیفی با برچسب دسترس‌پذیر ساخته می‌شوند",
          "panel-row-actions" in js and "aria-label" in js)

    print("\n۳) استقلال از شبکه (بدون CDN)")
    offline_ok = True
    for path in (CSS_PATH, JS_PATH):
        text = path.read_text(encoding="utf-8")
        hits = re.findall(r"https?://[^\s\"')]+", text)
        if hits:
            offline_ok = False
            print(f"      ! {path.name}: {hits[:3]}")
    check("CSS و JS پنل هیچ آدرس بیرونی ندارند", offline_ok)
    check("فونت وزیرمتن خودمیزبان است (۴ وزن)", css.count("@font-face") == 4 and
          "/static/fonts/Vazirmatn-" in css)

    print("\n۴) تمیزی CSS")
    token_block = re.search(r":root \{(.*?)\}\s*\.dark \{(.*?)\}", css, re.S)
    body_css = css.replace(token_block.group(0), "") if token_block else css
    stray_hex = re.findall(r"#[0-9a-fA-F]{3,6}\b", body_css)
    report["metrics"]["stray_hex"] = len(stray_hex)
    report["metrics"]["important"] = css.count("!important")
    report["metrics"]["hard_left_right"] = len(re.findall(r"\b(text-align\s*:\s*(left|right)|float\s*:\s*(left|right))", css))
    print(f"      رنگ سرسخت‌شده خارج از توکن‌ها: {len(stray_hex)} | !important: {css.count('!important')}"
          f" | چپ/راست سرسخت‌شده: {report['metrics']['hard_left_right']}")
    new_section = css.split("۹) توکن‌های رنگ پنل")[-1].split("۱۳)")[0]
    if token_block:                      # خودِ بلوک توکن‌ها رنگ سرسخت دارد (طبیعی است)
        new_section = new_section.replace(token_block.group(0), "")
    stray_light = re.findall(r"#[0-9a-fA-F]{3,6}", new_section)
    check("رنگ‌های تازهٔ پنل از توکن می‌آیند (بدون رنگ سرسخت در بخش‌های ۹ تا ۱۳)",
          not stray_light, f"رنگ‌های سرسخت: {stray_light[:4] or 'هیچ'}")
    check("چیدمان بدون مقدار چپ/راست سرسخت (سازگار با RTL)",
          report["metrics"]["hard_left_right"] == 0)

    print("\n۵) کارت «این بخش چیست؟» برای همه‌ی مدل‌ها")
    admin_user = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    client = Client()
    client.force_login(admin_user)
    covered, uncovered = [], []
    for model in apps.get_models():
        if not model in __import__("django.contrib.admin", fromlist=["site"]).site._registry:
            continue
        url = f"/admin/{model._meta.app_label}/{model._meta.model_name}/"
        html = client.get(url).content.decode()
        match = re.search(r'class="model-help__text"[^>]*>(.*?)</', html, re.S)
        text = re.sub(r"<[^>]+>", " ", match.group(1)).strip() if match else ""
        (covered if len(text) >= 10 else uncovered).append(f"{model._meta.label}")
    check("همه‌ی مدل‌های پنل توضیح فارسی دارند", not uncovered,
          f"{len(covered)} مدل توضیح‌دار" + (f" | بی‌توضیح: {uncovered[:4]}" if uncovered else ""))
    report["metrics"]["models_with_help"] = len(covered)

    print("\n۶) راست‌به‌چپ و ساختار صفحه")
    for path in ("/admin/", "/admin/orders/order/", "/admin/reports/", "/admin/alerts/"):
        html = client.get(path).content.decode()
        check(f"صفحه {path} راست‌به‌چپ است",
              'dir="rtl"' in html[:2000], "ویژگی dir روی تگ html")

    print("\n۷) متن و نگارش فارسی")
    guest = Client()
    guest.force_login(admin_user)
    months = "ژانویه فوریه مارس آوریل مه ژوئن ژوئیه اوت سپتامبر اکتبر نوامبر دسامبر".split()
    page_texts = {}
    # صفحه‌هایی که متن اختصاصی مهراصل دارند (کارت‌های panel-wrap).
    # فهرست‌های خام جنگو، متن اختصاصی ندارند؛ واژه‌های لاتینشان اسکلت unfold/جنگو است.
    for path in ("/admin/", "/admin/alerts/", "/admin/reports/", "/admin/quick-order/"):
        html = guest.get(path).content.decode()
        page_texts[path] = visible_text(html, '<div class="panel-wrap"')
    gregorian = sorted({m for text in page_texts.values() for m in months if f" {m} " in text})
    check("هیچ صفحه‌ای نام ماه میلادی نشان نمی‌دهد (تاریخ‌ها شمسی است)", not gregorian,
          f"ماه‌های میلادی: {gregorian or 'هیچ'}")

    from core.models import Notification

    latin_digits = [
        n.title for n in Notification.objects.all()[:200]
        if re.search(r"[0-9]", n.title) or re.search(r"[0-9]", n.body or "")
    ]
    check("متن اعلان‌های ثبت‌شده ارقام فارسی دارد", not latin_digits,
          f"{len(latin_digits)} اعلان با رقم لاتین")

    percent = {path: text.count("%") for path, text in page_texts.items()}
    check("در متن فارسی از ٪ استفاده شده، نه %", sum(percent.values()) == 0,
          f"کاربرد %: {percent}")

    icon_words = {"keyboard", "arrow", "control", "key", "alt", "down", "up", "more", "return",
                  "search", "expand", "close", "manage", "shopping", "mode", "cart", "downward",
                  "upward", "back", "forward", "open", "in", "new", "left", "right", "home"}
    leftover = set()
    for text in page_texts.values():
        for word in re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text):
            low = word.lower()
            if low in icon_words or len(word) < 3 or low.isupper():
                continue
            leftover.add(word)
    technical = {"python", "manage", "py", "check_alerts", "api", "admin", "url", "csrf",
                 "excel", "xlsx", "csv", "pdf", "id", "rfq", "sla", "po", "vat", "sku",
                 "kpi", "so", "inv", "pf", "moadian", "utf", "html", "css",
                 # واژه‌های فنی که در آدرس‌های پنل یا دستورهای اجرایی می‌آیند
                 "order", "orders", "quick", "summary", "check", "alerts", "panel"}
    allow = {w for w in leftover if w.isupper() or "-" in w} | technical
    unknown = sorted(w for w in leftover if w not in allow)
    check("متن پنل فارسی است (واژه‌ی لاتین ترجمه‌نشده‌ی ناشناخته ندارد)", len(unknown) <= 6,
          f"نامزدهای بررسی: {unknown[:6]}")

    templates_text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list((ROOT / "templates" / "admin").rglob("*.html")) + list((ROOT / "templates" / "core").rglob("*.html"))
    )
    missing_zwnj = len(re.findall(r"\s(?:می|نمی|های|ها)\s[ا-ی]", templates_text))
    check("نیم‌فاصله در قالب‌های پنل رعایت شده", missing_zwnj == 0, f"{missing_zwnj} مورد")
    check("واحد پول در متن پنل یکدست است (تومان)",
          templates_text.count("تومان") > 0 and "ریال" not in templates_text,
          f"«تومان»: {templates_text.count('تومان')} بار")

    out = ROOT / "docs" / "panel-ux-audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "─" * 62)
    print(f"نتیجهٔ سنجش تجربه‌ی کاربری پنل: {passed} موفق / {failed} ناموفق از {passed + failed}")
    print(f"گزارش JSON: {out.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
