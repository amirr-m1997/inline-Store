"""ساخت پیش‌نمایش تک‌فایلی (offline) از پنل واقعی در حال اجرا.

چرا؟ پیش‌نمایش زنده‌ی پنل به سرور Django وابسته است. این اسکریپت از همان صفحاتِ
واقعیِ در حال اجرا (با داده‌های واقعی پایگاه‌داده) یک فایل HTML مستقل می‌سازد که
همه‌چیز — CSS، فونت‌ها، نمودارها و آیکون‌ها — درون خودش است و بدون شبکه هم باز می‌شود.

اجرا (نیازی به سرور در حال اجرا نیست؛ از همان مدل‌ها و قالب‌های Django استفاده می‌شود):
    python3 scripts/build_static_preview.py                     # → ../mehrasl-panel-db-preview-v2.html
    python3 scripts/build_static_preview.py --out out.html
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PANEL_ROOT = BASE_DIR

PAGES = [
    ("dashboard", "داشبورد عملیاتی", "/admin/"),
    ("reports", "گزارش‌ها و خروجی اکسل", "/admin/reports/"),
    ("quick-order", "سفارش سریع", "/admin/quick-order/"),
    ("alerts", "مرکز اعلان‌ها", "/admin/alerts/"),
]

# چک‌لیست مدل‌ها: همان فهرست‌هایی که ادمین با query واقعی از پایگاه‌داده می‌سازد
CHANGELISTS = [
    ("products", "محصولات (کاتالوگ)", "/admin/catalog/product/", "catalog", "Product", ""),
    ("rfqs", "استعلام‌ها (RFQ)", "/admin/quotes/quote/", "quotes", "Quote", ""),
    ("orders-list", "سفارش‌ها", "/admin/orders/order/", "orders", "Order", "-id"),
    ("invoices", "فاکتورها", "/admin/finance/invoice/", "finance", "Invoice", "-id"),
    ("companies", "حساب‌های سازمانی", "/admin/customers/company/", "customers", "Company", ""),
    ("stock", "موجودی انبار", "/admin/inventory/stockitem/", "inventory", "StockItem", ""),
    ("cheques", "چک‌ها و سررسید", "/admin/finance/cheque/", "finance", "Cheque", "due_date"),
    ("pricelists", "سبدهای قیمت", "/admin/pricing/pricelist/", "pricing", "PriceList", ""),
    ("payments", "پرداخت‌ها", "/admin/finance/payment/", "finance", "Payment", "-id"),
    ("purchase-requests", "درخواست‌های خرید", "/admin/inventory/purchaserequest/",
     "inventory", "PurchaseRequest", "-id"),
    ("notifications", "اعلان‌های ثبت‌شده", "/admin/core/notification/", "core", "Notification", "-id"),
    ("approvals", "مراحل گردش تأیید", "/admin/orders/approval/", "orders", "Approval", "-id"),
    ("company-users", "کاربران پنل مشتری", "/admin/customers/companyuser/",
     "customers", "CompanyUser", ""),
    ("audit", "سیاههٔ حسابرسی", "/admin/core/auditlog/", "core", "AuditLog", "-id"),
]

# موجودی واقعی پایگاه‌داده برای بخش «منبع داده»
DB_MODELS = [
    ("catalog", "Product", "محصول"), ("catalog", "Brand", "برند"), ("catalog", "Category", "دسته‌بندی"),
    ("catalog", "ProductDocument", "سند فنی"), ("catalog", "SpecTemplate", "قالب مشخصات فنی"),
    ("catalog", "ProductImage", "تصویر محصول"), ("catalog", "ProductRelation", "رابطه کالا"),
    ("pricing", "PriceList", "سبد قیمت"), ("pricing", "PriceListItem", "ردیف قیمت"),
    ("pricing", "QuantityPriceBreak", "قیمت پلکانی حجمی"),
    ("inventory", "Warehouse", "انبار"), ("inventory", "StockItem", "موجودی"),
    ("inventory", "StockMove", "تراکنش انبار"), ("inventory", "PurchaseRequest", "درخواست خرید"),
    ("customers", "Company", "حساب سازمانی"), ("customers", "CompanyUser", "کاربر مشتری"),
    ("customers", "CompanyAddress", "نشانی"),
    ("quotes", "Quote", "استعلام"), ("quotes", "QuoteLine", "ردیف استعلام"),
    ("quotes", "QuoteMessage", "پیام مذاکره"),
    ("orders", "Order", "سفارش"), ("orders", "OrderLine", "ردیف سفارش"),
    ("orders", "OrderEvent", "رخداد سفارش"), ("orders", "Approval", "مرحله تأیید"),
    ("orders", "ApprovalRule", "قاعده تأیید"),
    ("finance", "Invoice", "فاکتور"), ("finance", "InvoiceLine", "ردیف فاکتور"),
    ("finance", "Payment", "پرداخت"), ("finance", "Cheque", "چک"),
    ("core", "Notification", "اعلان"), ("core", "AuditLog", "رخداد حسابرسی"),
    ("accounts", "Profile", "پروفایل کاربر"),
]

# آیکون‌های استفاده‌شده در قالب‌های پنل → مسیر SVG (خطی، هم‌سبک با طرح تأییدشده)
ICONS = {
    "trending_up": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "forum": '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "approval": '<path d="M9 3h6a1 1 0 0 1 1 1v1h2a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h2V4a1 1 0 0 1 1-1z"/>'
                '<path d="M9 13l2.5 2.5L16 10"/>',
    "inventory_2": '<path d="M3 7l2-3h14l2 3v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M3 7h18"/><path d="M9 12h6"/>',
    "account_balance_wallet": '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M2 10h20"/><circle cx="17" cy="14" r="1.2"/>',
    "notifications_active": '<path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6"/><path d="M10.5 20a1.8 1.8 0 0 0 3 0"/>',
    "priority_high": '<path d="M12 4v10"/><circle cx="12" cy="19" r="1.4"/>',
    "warning": '<path d="M12 3 2 20h20z"/><path d="M12 9v5"/><circle cx="12" cy="17.3" r="1"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="8" r="1"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/>',
    "check_small": '<path d="M5 13l4 4L19 7"/>',
    "check": '<path d="M5 13l4 4L19 7"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "home": '<path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z"/>',
}

SIDEBAR = [
    ("عملیات فروش", [
        ("داشبورد عملیاتی", "dashboard"),
        ("گزارش‌ها و خروجی اکسل", "reports"),
        ("سفارش سریع", "quick-order"),
        ("اعلان‌ها و هشدارها", "alerts"),
        ("استعلام‌ها (داده)", "rfqs"),
        ("سفارش‌ها (داده)", "orders-list"),
    ]),
    ("کاتالوگ و قیمت", [
        ("محصولات", "products"), ("سبدهای قیمت", "pricelists"),
        ("دسته‌بندی‌ها", None), ("قالب مشخصات فنی", None), ("قیمت پلکانی حجمی", None),
    ]),
    ("انبار", [
        ("موجودی", "stock"), ("درخواست خرید", "purchase-requests"), ("رسید و حواله", None),
    ]),
    ("مشتریان و مالی", [
        ("حساب‌های سازمانی", "companies"), ("کاربران مشتری", "company-users"),
        ("فاکتورها", "invoices"), ("چک‌ها و سررسید", "cheques"), ("پرداخت‌ها", "payments"),
    ]),
    ("گردش تأیید", [
        ("مراحل تأیید", "approvals"), ("اعلان‌های ثبت‌شده", "notifications"),
    ]),
    ("مدیریت", [
        ("سیاههٔ حسابرسی", "audit"), ("منبع داده", "data-source"),
        ("کاربران و نقش‌ها", None),
    ]),
]

ADMIN_MODELS_ROWS = [
    ("کاتالوگ", "محصول", "۳۶ کالا، ۱۰ ستون، ۶ فیلتر، ۴ اکشن گروهی، inline اسناد/موجودی/تصاویر"),
    ("قیمت‌گذاری", "سبد قیمت + قیمت پلکانی حجمی", "۵ سبد، ۱۴ ردیف قیمت، ۱۳ پله — با بازهٔ اعتبار"),
    ("انبار", "موجودی و تراکنش", "۳ انبار، ۳۴ قلم موجودی، ۳۰ رسید/حواله"),
    ("مشتریان", "حساب سازمانی", "۱۴ حساب، اعتبار/KYC، کاربران و نشانی‌ها"),
    ("استعلام", "RFQ + مکاتبه", "۳۴ استعلام با SLA، ۳ اکشن رکوردی (ارسال، تبدیل، تخصیص)"),
    ("سفارش", "سفارش + گردش تأیید", "۹۶ سفارش، ۴ اکشن رکوردی، خط زمانی و تأییدیه‌ها"),
    ("مالی", "فاکتور، پرداخت، چک", "۷۳ فاکتور، ۴۲ پرداخت، ۴۰ چک + سامانه مؤدیان"),
    ("هسته", "سیاههٔ حسابرسی", "۱٬۴۷۹ رخداد، ثبت قبل/بعد، فیلتر و جست‌وجو"),
]


# ------------------------------------------------------------------ ابزار صفحه‌گیری
def make_client():
    """کلاینت تست جنگو با کاربر مدیر (همان مسیر واقعی رندر قالب‌ها)."""
    if str(PANEL_ROOT) not in sys.path:
        sys.path.insert(0, str(PANEL_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.contrib.auth import get_user_model
    from django.test import Client

    user = (get_user_model().objects.filter(is_superuser=True).order_by("id").first()
            or get_user_model().objects.order_by("id").first())
    if user is None:
        raise SystemExit("کاربری در پایگاه‌داده نیست؛ ابتدا «python manage.py seed_demo» را اجرا کنید.")
    client = Client()
    client.force_login(user)
    return client


def font_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:font/woff2;base64,{encoded}"


# ------------------------------------------------------------ استخراج و پاک‌سازی
def extract_panel_block(html: str) -> str:
    """استخراج بلوک <div class="panel-wrap">…</div> با تطبیق عمق تگ‌ها."""
    start = html.find('<div class="panel-wrap"')
    if start == -1:
        raise SystemExit("بلوک panel-wrap در صفحه پیدا نشد")
    depth = 0
    index = start
    token = re.compile(r"<div\b|</div>")
    while True:
        match = token.search(html, index)
        if not match:
            raise SystemExit("بستن بلوک panel-wrap پیدا نشد")
        if match.group(0).startswith("<div"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return html[start:match.end()]
        index = match.end()


def replace_icons(block: str) -> str:
    def to_svg(match: re.Match) -> str:
        name = match.group(1).strip()
        paths = ICONS.get(name, ICONS["info"])
        return (f'<svg class="msi" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')

    return re.sub(r'<span class="material-symbols-outlined">\s*([a-z_0-9]+)\s*</span>', to_svg, block)


def neutralize_links(block: str) -> str:
    block = re.sub(r'href="/admin[^"]*"', 'href="#" onclick="return false"', block)
    block = re.sub(r'action="/admin[^"]*"', 'action="#" onsubmit="return false"', block)
    return block


def strip_scripts(block: str) -> str:
    return re.sub(r"<script\b.*?</script>", "", block, flags=re.S)


# ------------------------------------------------- تبدیل چک‌لیست ادمین به جدول پنل
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(value) -> str:
    """عدد را با جداکننده و ارقام فارسی برمی‌گرداند (هم‌سبک با بقیه‌ی پنل)."""
    return f"{int(value):,}".translate(_DIGITS)


def _clean_cell(fragment: str) -> str:
    """سلول جدول ادمین را برای نمایش آفلاین پاک می‌کند.

    ترتیب مهم است: ابتدا وضعیت چک‌باکس‌ها به علامت خوانا تبدیل می‌شود، سپس آیکون‌ها،
    و در پایان صفت‌های کلاس/Django حذف می‌شوند (فقط `style` و `href` نگه داشته می‌شوند
    چون برچسب‌های رنگی پنل استایل درون‌خطی دارند).
    """
    # ۱) چک‌باکس‌های list_editable → ✓ / ✗ (پیش از حذف inputها و صفت‌ها)
    def _checkbox(match: re.Match) -> str:
        tag = match.group(0)
        # صفت واقعی checked (نه کلاس‌های tailwind مثل checked:bg-primary-600)
        is_checked = bool(re.search(r"\schecked(?:\s|=|/?>)", tag))
        return ('<span style="color:#12855f;font-weight:700">✓</span>' if is_checked
                else '<span style="color:#b45309;font-weight:700">✗</span>')

    fragment = re.sub(r"<input[^>]*type=\"checkbox\"[^>]*>", _checkbox, fragment)
    fragment = re.sub(r"<input\b[^>]*>", "", fragment)

    # ۱٫۵) چیپ‌های بولین ادمین (بله/خیر) → برچسب رنگی پنل
    def _boolean_chip(match: re.Match) -> str:
        attrs = match.group(1)
        classes = match.group(0).split('class="', 1)[1].split('"', 1)[0]
        title_search = re.search(r'title="([^"]*)"', attrs + match.group(0))
        title = title_search.group(1) if title_search else ""
        color = "#12855f" if "green" in classes else ("#c02626" if "red" in classes else "#64748b")
        label = title or ("بله" if "green" in classes else "خیر")
        return (f'<span style="background:{color}1a;color:{color};padding:2px 8px;'
                f'border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap">{label}</span>')

    fragment = re.sub(
        r'<div class="inline-flex[^"]*"([^>]*)>\s*'
        r'<span class="material-symbols-outlined">\s*[a-z_0-9]+\s*</span>\s*</div>',
        _boolean_chip, fragment, flags=re.S)

    # ۲) آیکون‌های Material Symbols → SVG خطی
    fragment = re.sub(r'<span class="material-symbols-outlined">\s*([a-z_0-9]+)\s*</span>',
                      lambda m: replace_icons(m.group(0)), fragment)
    # ۳) آیکون‌های تعاملی ادمین (SVG بدون کلاس msi) در نسخهٔ ثابت معنا ندارند
    fragment = re.sub(r"<svg(?![^>]*class=\"msi\")[^>]*>.*?</svg>", "", fragment, flags=re.S)
    # ۴) حذف صفت‌های غیرلازم (کلاس‌ها، رویدادها، نام‌های فرم)
    fragment = re.sub(r"\s(?!style=|href=)[a-zA-Z-:]+=\"[^\"]*\"", "", fragment)
    fragment = re.sub(r'href="/admin[^"]*"', 'href="#"', fragment)
    fragment = re.sub(r"<div[^>]*>\s*</div>", "", fragment)
    fragment = _strip_icon_words(fragment)
    fragment = re.sub(r"\s+", " ", fragment).strip()
    if not re.sub(r"<[^>]+>", "", fragment).strip():   # فقط تگ مانده، بدون متن
        return "—"
    return fragment


ICON_WORD_RE = re.compile(
    r"\b(?:arrow_circle_down|arrow_circle_up|arrow_upward_alt|arrow_downward_alt|unfold_more|"
    r"unfold_less|keyboard_return|keyboard_control_key|check_small|close|cancel|search|add|remove|"
    r"toggle_on|toggle_off|drag_indicator|sort)\b"
)


def _strip_icon_words(text: str) -> str:
    """واژه‌های لیگاتور آیکون‌ها (که در فقدان فونت به‌صورت متن دیده می‌شوند) را حذف می‌کند."""
    return ICON_WORD_RE.sub(" ", text)


def convert_changelist(page: str) -> tuple[list[str], list[list[str]]]:
    """(سرستون‌ها، ردیف‌ها) را از جدول result_list صفحهٔ ادمین بیرون می‌کشد.

    نکته: unfold هر ردیف را در `<tbody>` جداگانه می‌پیچد؛ پس بدنه با تطبیق
    حریصانه تا آخرین `</tbody>` برداشته می‌شود.
    """
    table_match = re.search(r'<table id="result_list".*?</table>', page, re.S)
    if not table_match:
        return [], []
    table = table_match.group(0)
    head = re.search(r"<thead\b[^>]*>(.*?)</thead>", table, re.S)
    headers: list[str] = []
    if head:
        for tag, cell in re.findall(r"<th\b([^>]*)>(.*?)</th>", head.group(1), re.S):
            if "action-checkbox" in tag:
                continue
            text = _strip_icon_words(re.sub(r"<[^>]+>", " ", cell))
            headers.append(re.sub(r"\s+", " ", text).strip() or "—")
    body = re.search(r"<tbody\b[^>]*>(.*)</tbody>", table, re.S)
    raw_rows: list[list[str]] = []
    if body:
        for row_html in re.findall(r"<tr\b.*?</tr>", body.group(1), re.S):
            if 'colspan="' in row_html and len(re.findall(r"<t[dh]\b", row_html)) == 1:
                continue  # ردیف «نتیجه‌ای یافت نشد»
            raw_rows.append([
                cell
                for tag, cell in re.findall(r"<t[dh]\b([^>]*)>(.*?)</t[dh]>", row_html, re.S)
                if "action-checkbox" not in tag          # ستون چک‌باکس انتخاب گروهی
            ])

    # ستون‌های «اکشن‌های ردیف» (منوی Alpine) در نسخهٔ ثابت معنا ندارند → حذف ستون
    def _is_action_column(index: int) -> bool:
        if not raw_rows:
            return False
        hits = sum(1 for row in raw_rows
                   if index < len(row) and ("x-on:click" in row[index] or "x-bind" in row[index]))
        return hits >= max(1, int(len(raw_rows) * 0.8))

    if raw_rows:
        width = max(len(row) for row in raw_rows)
        drop = {i for i in range(width) if _is_action_column(i)}
        if drop:
            headers = [h for i, h in enumerate(headers) if i not in drop]
            raw_rows = [[c for i, c in enumerate(row) if i not in drop] for row in raw_rows]

    rows = [[_clean_cell(cell) for cell in row] for row in raw_rows if row]
    return headers, rows


def extract_model_help(page: str) -> str:
    """کارت «این بخش چیست؟» را از صفحهٔ ادمین برمی‌دارد و به سبک پیش‌نمایش برمی‌گرداند."""
    match = re.search(r'<div class="model-help"[^>]*>(.*?)</div>\s*</div>', page, re.S)
    if not match:
        match = re.search(r'<div class="model-help"[^>]*>(.*?)</div>', page, re.S)
    if not match:
        return ""
    inner = match.group(1)
    text_match = re.search(r'model-help__text">(.*?)</span>', inner, re.S)
    if not text_match:
        return ""
    text = re.sub(r"<[^>]+>", " ", text_match.group(1))
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return f'<p class="pv-note pv-note--help"><b>این بخش چیست؟</b> {html_lib.escape(text)}</p>'


def django_count(app_label: str, model_name: str) -> int:
    from django.apps import apps as django_apps

    return django_apps.get_model(app_label, model_name)._default_manager.count()


def built_at_jalali() -> str:
    """زمان ساخت پیش‌نمایش به تاریخ و ساعت شمسی."""
    import jdatetime

    from django.utils import timezone

    now = timezone.localtime()
    jalali = jdatetime.datetime.fromgregorian(datetime=now)
    digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return (f"{jalali.year}/{jalali.month:02d}/{jalali.day:02d} — "
            f"{jalali.hour:02d}:{jalali.minute:02d}").translate(digits)


def database_inventory() -> tuple[list[tuple[str, str, int]], str]:
    """موجودی واقعی پایگاه‌داده (تعداد رکورد هر مدل + مشخصات فایل/موتور)."""
    from django.conf import settings
    from django.db import connection

    rows = [(label, f"{app_label}.{model_name}", django_count(app_label, model_name))
            for app_label, model_name, label in DB_MODELS]
    path = Path(str(settings.DATABASES["default"]["NAME"]))
    size = f"{path.stat().st_size / 1024:.0f} کیلوبایت" if path.exists() else "—"
    return rows, f"{connection.vendor} — {path.name} ({size})"


# ------------------------------------------------------------------ ساخت فایل
def quick_order_preview(client) -> str:
    """صفحه‌ی سفارش سریع با یک فهرست نمونه، تا جدول تطبیق/قیمت‌گذاری در پیش‌نمایش دیده شود."""
    from customers.models import Company

    company = Company.objects.filter(is_active=True).order_by("name").first()
    if company is None:
        return fetch_page(client, "/admin/quick-order/")
    lines = "FC-600 × 12\nCH-TR-060 × 2\nCL-CU-038, 240\nAHU-5000 × 1\nIN-EL-13 × 60\nXX-999 × 3"
    response = client.post("/admin/quick-order/",
                           {"company": company.pk, "lines": lines, "action": "preview"})
    return response.content.decode("utf-8")


def fetch_page(client, path: str, data: dict | None = None) -> str:
    response = client.post(path, data) if data else client.get(path)
    return response.content.decode("utf-8")


def build(out: Path) -> tuple[Path, int]:
    css = (PANEL_ROOT / "static/css/panel.css").read_text(encoding="utf-8")
    font_dir = PANEL_ROOT / "static/fonts"
    for weight, name in (("400", "Regular"), ("500", "Medium"), ("600", "SemiBold"), ("700", "Bold")):
        uri = font_data_uri(font_dir / f"Vazirmatn-{name}.woff2")
        css = css.replace(f'url("/static/fonts/Vazirmatn-{name}.woff2")', f"url({uri})")

    client = make_client()
    sections = []
    meta = []
    for key, title, path in PAGES:
        page = quick_order_preview(client) if key == "quick-order" else fetch_page(client, path)
        block = extract_panel_block(page)
        block = strip_scripts(block)
        block = replace_icons(block)
        block = neutralize_links(block)
        active = " is-active" if not meta else ""
        open_tag = f'<section class="pv-view{active}" id="pv-{key}">'
        sections.append(f'{open_tag}{block}</section>')
        meta.append((key, title))

    sidebar_html = []
    for group_title, items in SIDEBAR:
        links = "".join(
            (f'<a class="pv-nav-link is-active" data-target="pv-{key}" href="#">{label}</a>'
             if key else f'<a class="pv-nav-link" href="#">{label}</a>')
            for label, key in items
        )
        sidebar_html.append(f'<div class="pv-nav-group"><span>{group_title}</span>{links}</div>')
    sidebar_html = "".join(sidebar_html)

    # --------------------------------------------- چک‌لیست‌های واقعی از پایگاه‌داده
    for key, title, path, app_label, model_name, ordering in CHANGELISTS:
        url = path + (f"?o={ordering}" if ordering else "")
        page = fetch_page(client, url)
        headers, rows = convert_changelist(page)
        total = django_count(app_label, model_name)
        head_html = "".join(f"<th>{html_lib.escape(header)}</th>" for header in headers)
        if rows:
            body_html = "".join(
                "<tr>" + "".join(f'<td class="panel-mono">{cell}</td>' for cell in row) + "</tr>"
                for row in rows
            )
        else:
            body_html = (f'<tr><td colspan="{max(len(headers), 1)}" class="panel-empty">'
                         f'رکوردی برای نمایش نیست.</td></tr>')
        meta.append((key, title))
        help_html = extract_model_help(page)
        sections.append(f'''<section class="pv-view" id="pv-{key}">
  {help_html}
  <section class="panel-card">
    <header class="panel-card-head">
      <div><b>{title}</b>
        <span class="panel-sub">این جدول با query واقعی از پایگاه‌داده ساخته شده —
          {fa_num(total)} رکورد در جدول، نمایش {fa_num(len(rows))} ردیف اول</span></div>
      <div class="panel-card-actions"><span class="panel-chip">{path}</span></div>
    </header>
    <div class="panel-card-body panel-tight">
      <table class="panel-table">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{body_html}</tbody>
      </table>
    </div>
  </section>
</section>''')

    # ------------------------------------------------- بخش «منبع داده» (DB)
    db_rows, db_desc = database_inventory()
    db_total = sum(count for _label, _model, count in db_rows)
    has_data = len([row for row in db_rows if row[2]])
    db_kpis = {
        "total": fa_num(db_total), "models": fa_num(has_data),
        "orders": fa_num(django_count("orders", "Order")),
        "quotes": fa_num(django_count("quotes", "Quote")),
        "invoices": fa_num(django_count("finance", "Invoice")),
        "audit": fa_num(django_count("core", "AuditLog")),
    }
    db_table = "".join(
        f"<tr><td>{html_lib.escape(label)}</td><td class='panel-mono'>{model}</td>"
        f"<td class='panel-mono'>{fa_num(count)}</td></tr>"
        for label, model, count in db_rows
    )
    meta.append(("data-source", "منبع داده"))
    sections.append(f'''<section class="pv-view" id="pv-data-source">
  <div class="panel-kpi-row">
    <div class="panel-kpi"><div class="panel-kpi-top"><span class="panel-kpi-label">رکوردهای پایگاه‌داده</span></div>
      <div class="panel-kpi-value">{db_kpis["total"]}</div>
      <div class="panel-kpi-foot"><span>در {db_kpis["models"]} مدل دارای داده</span></div></div>
    <div class="panel-kpi"><div class="panel-kpi-top"><span class="panel-kpi-label">سفارش‌ها</span></div>
      <div class="panel-kpi-value">{db_kpis["orders"]}</div>
      <div class="panel-kpi-foot"><span>سفارش ثبت‌شده در سیستم</span></div></div>
    <div class="panel-kpi"><div class="panel-kpi-top"><span class="panel-kpi-label">استعلام‌ها</span></div>
      <div class="panel-kpi-value">{db_kpis["quotes"]}</div>
      <div class="panel-kpi-foot"><span>RFQ ثبت‌شده</span></div></div>
    <div class="panel-kpi"><div class="panel-kpi-top"><span class="panel-kpi-label">فاکتورها</span></div>
      <div class="panel-kpi-value">{db_kpis["invoices"]}</div>
      <div class="panel-kpi-foot"><span>فاکتور صادرشده</span></div></div>
    <div class="panel-kpi"><div class="panel-kpi-top"><span class="panel-kpi-label">رخداد حسابرسی</span></div>
      <div class="panel-kpi-value">{db_kpis["audit"]}</div>
      <div class="panel-kpi-foot"><span>ثبت قبل/بعد تغییرات</span></div></div>
  </div>

  <section class="panel-card">
    <header class="panel-card-head">
      <div><b>منبع داده‌ی همین پیش‌نمایش</b>
        <span class="panel-sub">همه‌ی جدول‌ها و نمودارهای این فایل، همین حالا از پایگاه‌داده خوانده شده‌اند —
        {db_desc} · زمان ساخت: {built_at_jalali()}</span></div>
    </header>
    <div class="panel-card-body panel-tight">
      <table class="panel-table">
        <thead><tr><th>موجودیت</th><th>مدل Django</th><th>تعداد رکورد</th></tr></thead>
        <tbody>{db_table}</tbody>
      </table>
    </div>
  </section>
</section>''')

    tabs = "".join(
        f'<button class="pv-tab{" is-active" if i == 0 else ""}" data-target="pv-{key}">{title}</button>'
        for i, (key, title) in enumerate(meta)
    )

    model_rows = "".join(
        f"<tr><td>{app}</td><td>{model}</td><td>{desc}</td></tr>" for app, model, desc in ADMIN_MODELS_ROWS
    )

    banner = (f"داده‌های این پیش‌نمایش همین حالا از پایگاه‌داده خوانده شده است — {db_desc} · "
              f"{db_kpis['total']} رکورد در {db_kpis['models']} مدل · "
              f"{db_kpis['orders']} سفارش · {db_kpis['quotes']} استعلام · {db_kpis['invoices']} فاکتور · "
              f"زمان ساخت: {built_at_jalali()}")

    document = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پیش‌نمایش پنل مدیریت مهراصل</title>
<style>
{css}

/* ---------------------------------------------------------- پوسته‌ی پیش‌نمایش */
:root {{ --pv-navy:#0d1a2b; --pv-navy2:#132540; --pv-line:#e6eaf2; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: #f4f6fb; color: #0f1b2d;
  font-family: "Vazirmatn", "IRANSansX", Tahoma, system-ui, sans-serif;
}}
.pv-shell {{ display: flex; min-height: 100vh; }}
.pv-side {{
  width: 246px; flex: 0 0 246px; background: linear-gradient(180deg, var(--pv-navy), var(--pv-navy2));
  color: #cbd6e6; padding: 16px 14px; position: sticky; top: 0; height: 100vh; overflow: auto;
}}
.pv-logo {{ display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }}
.pv-logo i {{
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  background: linear-gradient(135deg, #0e7490, #0891b2); color: #fff;
}}
.pv-logo b {{ color: #fff; font-size: 13.5px; display: block; }}
.pv-logo small {{ font-size: 11px; color: #8fa3bd; }}
.pv-nav-group {{ margin-bottom: 16px; }}
.pv-nav-group > span {{ font-size: 10.5px; color: #6f85a3; letter-spacing: .2px; }}
.pv-nav-link {{
  display: block; padding: 7px 9px; margin-top: 5px; border-radius: 9px;
  color: #cbd6e6; font-size: 12.4px; text-decoration: none; cursor: pointer;
}}
.pv-nav-link:hover {{ background: rgba(255,255,255,.06); }}
.pv-nav-link.is-active {{ background: linear-gradient(90deg, rgba(8,145,178,.35), rgba(8,145,178,.05)); color: #fff; }}
.pv-main {{ flex: 1; min-width: 0; }}
.pv-top {{
  background: #fff; border-bottom: 1px solid var(--pv-line); padding: 12px 20px;
  display: flex; align-items: center; gap: 14px; position: sticky; top: 0; z-index: 5;
}}
.pv-top h1 {{ font-size: 14px; margin: 0; font-weight: 700; }}
.pv-top .pv-env {{
  background: #fff7e6; color: #b45309; border: 1px solid #ffe0b2;
  border-radius: 8px; padding: 2px 8px; font-size: 10.5px; font-weight: 600;
}}
.pv-user {{ margin-inline-start: auto; display: flex; align-items: center; gap: 8px; font-size: 12px; color: #5b6b82; }}
.pv-avatar {{
  width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center;
  background: #0e7490; color: #fff; font-size: 11px; font-weight: 700;
}}
.pv-tabs {{ display: flex; gap: 6px; flex-wrap: wrap; padding: 14px 20px 0; }}
.pv-tab {{
  border: 1px solid var(--pv-line); background: #fff; color: #5b6b82; cursor: pointer;
  border-radius: 999px; padding: 7px 14px; font: inherit; font-size: 12.3px;
}}
.pv-tab.is-active {{ background: #0e7490; border-color: #0e7490; color: #fff; font-weight: 600; }}
.pv-body {{ padding: 14px 20px 40px; }}
.pv-view {{ display: none; }}
.pv-view.is-active {{ display: block; }}
.msi {{ width: 17px; height: 17px; display: block; }}
.panel-kpi-icon svg {{ width: 16px; height: 16px; }}
.pv-note {{
  margin: 0 20px 6px; background: #eef7fb; border: 1px solid #cfe9f4; color: #0e5d75;
  border-radius: 12px; padding: 10px 12px; font-size: 12px; line-height: 1.9;
}}
.pv-note b {{ color: #0b4a5c; }}
.pv-note--db {{ background: #0d1a2b; color: #d7e3f2; border-color: #0d1a2b; }}
.pv-note--db b {{ color: #7fd7ea; }}
.pv-models {{ width: 100%; border-collapse: collapse; font-size: 12.3px; }}
.pv-models th, .pv-models td {{ border-bottom: 1px solid var(--pv-line); padding: 8px 10px; text-align: right; }}
.pv-models th {{ background: #f8fafd; color: #5b6b82; font-weight: 600; }}
.pv-note--help {{ background: #f0f9fb; border-color: #cdeaf1; color: #334155; text-align: right; }}
.pv-note--help b {{ color: #0e7490; }}
.pv-foot {{ color: #5b6b82; font-size: 11.5px; padding: 0 20px 26px; }}
@media (max-width: 900px) {{
  .pv-side {{ display: none; }}
}}
</style>
</head>
<body>
<div class="pv-shell">
  <aside class="pv-side">
    <div class="pv-logo">
      <i><svg class="msi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
        stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M3 8l9 4 9-4M3 16l9-4 9 4"/></svg></i>
      <div><b>پنل مدیریت مهراصل</b><small>مرکز عملیات فروش B2B</small></div>
    </div>
    {sidebar_html}
  </aside>

  <main class="pv-main">
    <header class="pv-top">
      <h1>مرکز عملیات فروش B2B</h1>
      <span class="pv-env">استیجینگ</span>
      <div class="pv-user">
        <span>رضا محمدی — مدیر فروش</span>
        <span class="pv-avatar">ر.م</span>
      </div>
    </header>

    <div class="pv-note pv-note--db">
      <b>منبع داده:</b> {banner}
    </div>

    <div class="pv-note">
      این فایل، <b>عکس فوری تک‌فایلی از پنل واقعی در حال اجرا</b> است: همان HTMLِ تولیدشده توسط Django،
      با داده‌های زندهٔ پایگاه‌داده (۹۶ سفارش، ۳۴ استعلام، ۷۳ فاکتور). CSS، فونت وزیرمتن، آیکون‌ها و نمودارها
      همه درون همین فایل‌اند؛ بنابراین بدون اینترنت و بدون سرور هم دقیقاً همان شکل پنل را نشان می‌دهد.
      لینک‌ها و فرم‌ها در این نسخه غیرفعال‌اند — برای تعامل واقعی از پیش‌نمایش زندهٔ پنل (پورت ۸۰۰۰) استفاده کنید.
    </div>

    <nav class="pv-tabs">{tabs}</nav>

    <div class="pv-body">
      {''.join(sections)}

      <div class="panel-wrap">
        <section class="panel-card" id="pv-models-card">
          <header class="panel-card-head">
            <div><b>مدل‌ها روی صفحه‌های پنل</b>
              <span class="panel-sub">۳۲ مدل دامنه — همه با فهرست، فیلتر، جست‌وجو و فرم ویرایش</span></div>
          </header>
          <div class="panel-card-body panel-tight">
            <table class="pv-models">
              <thead><tr><th>اپ</th><th>مدل</th><th>وضعیت روی پنل</th></tr></thead>
              <tbody>{model_rows}</tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </main>
</div>

<script>
document.querySelectorAll(".pv-tab, .pv-nav-link[data-target]").forEach(function (el) {{
  el.addEventListener("click", function () {{
    var target = el.getAttribute("data-target");
    document.querySelectorAll(".pv-view").forEach(function (v) {{
      v.classList.toggle("is-active", v.id === target);
    }});
    document.querySelectorAll(".pv-tab").forEach(function (t) {{
      t.classList.toggle("is-active", t.getAttribute("data-target") === target);
    }});
    window.scrollTo({{ top: 0, behavior: "smooth" }});
  }});
}});
var first = document.querySelector(".pv-view");
if (first) first.classList.add("is-active");
</script>
</body>
</html>
"""
    out.write_text(document, encoding="utf-8")
    return out, len(document.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="ساخت پیش‌نمایش تک‌فایلی آفلاین از پنل در حال اجرا")
    parser.add_argument("--out", default=str(PANEL_ROOT.parent / "mehrasl-panel-db-preview-v2.html"))
    options = parser.parse_args()

    path, size = build(Path(options.out))
    print(f"پیش‌نمایش ساخته شد: {path} ({size / 1024:.0f} کیلوبایت)")


if __name__ == "__main__":
    main()
