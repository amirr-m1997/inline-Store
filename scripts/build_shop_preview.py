"""ساخت پیش‌نمایش تک‌فایلی از سایت مشتری مهراصل (خروجی واقعی قالب‌ها).

    python3 scripts/build_shop_preview.py [خروجی]

چه می‌کند:
۱) با ابزار آزمون جنگو، صفحه‌های واقعی فروشگاه را از دیتابیس فعلی رندر می‌کند
   (مهمان + مشتری واردشده با سبد پر)؛ هیچ داده‌ای در دیتابیس تغییر نمی‌کند.
۲) CSS سایت را با فونت وزیرمتن به‌صورت base64 داخل فایل می‌گذارد تا بدون اینترنت هم کامل باشد.
۳) خروجی یک فایل HTML خودبسنده است با کلید تم روشن/تیره و فهرست بخش‌ها.
"""
from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/user/mehrasl-shop-preview.html")


def font_css() -> str:
    parts = []
    for weight, name in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")):
        path = BASE / "static" / "fonts" / f"Vazirmatn-{name}.woff2"
        if not path.exists():
            continue
        data = base64.b64encode(path.read_bytes()).decode()
        parts.append(
            "@font-face{font-family:'Vazirmatn';font-style:normal;font-weight:%d;"
            "src:url(data:font/woff2;base64,%s) format('woff2');font-display:swap}" % (weight, data)
        )
    return "\n".join(parts)


def css_text() -> str:
    css = (BASE / "static" / "css" / "shop.css").read_text(encoding="utf-8")
    css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)  # فونت‌ها با نسخهٔ base64 جایگزین می‌شوند
    return font_css() + "\n" + css


def clean(html: str, *, full: bool) -> str:
    """حذف وابستگی‌های بیرونی و بی‌اثر کردن لینک/فرم‌ها در پیش‌نمایش."""
    if full:
        body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
        chunk = body_match.group(1) if body_match else html
    else:
        body_match = re.search(r"<main id=\"main\"[^>]*>(.*?)</main>", html, re.S)
        chunk = body_match.group(1) if body_match else html
    chunk = re.sub(r"<script[^>]*>.*?</script>", "", chunk, flags=re.S)
    chunk = re.sub(r'<script[^>]*src="[^"]*"[^>]*>\s*</script>', "", chunk)
    chunk = re.sub(r'href="(?!/|#|https?:)[^"]*"', 'href="#"', chunk)
    chunk = re.sub(r'href="/(?!#)[^"]*"', 'href="#"', chunk)
    chunk = re.sub(r"<form\b", '<form onsubmit="return false"', chunk)
    chunk = re.sub(r'<!--.*?-->', "", chunk, flags=re.S)
    return chunk.strip()


def build() -> Path:
    from catalog.models import Product

    product = Product.objects.filter(is_active=True, code="FC-600").first() or Product.objects.filter(is_active=True).first()

    anon = Client()
    buyer = Client()
    logged_in = buyer.login(username="cu0-admin", password="Mehr@1405")
    if logged_in and product is not None:
        buyer.post(reverse("shop:cart-add", args=[product.pk]), {"qty": "10"})
        second = Product.objects.filter(is_active=True).exclude(pk=product.pk).order_by("?")[:2]
        for p in second:
            buyer.post(reverse("shop:cart-add", args=[p.pk]), {"qty": "5"})

    pages: list[tuple[str, str, str, object, bool]] = []  # (عنوان, توضیح, url, client, full)

    def add(title, note, url, client=anon, full=False):
        pages.append((title, note, url, client, full))

    add("صفحهٔ اصلی (فهرست کالاها)", "سربرگ، هیرو، کارت کالا، فیلترها و فوتر — نمای مهمان",
        reverse("shop:home"), anon, True)
    from finance.models import Invoice
    from orders.models import Order

    company_orders = (Order.objects.filter(company__users__user__username="cu0-admin")
                      .select_related("company").order_by("-ordered_at"))
    order = company_orders.first()
    invoices = list(Invoice.objects.filter(company_id=1).select_related("order").order_by("-issued_at"))
    invoice = (next((inv for inv in invoices if inv.kind == "proforma"), None)
               or next((inv for inv in invoices if inv.balance == 0), None)
               or (invoices[0] if invoices else None))
    if invoice is not None and invoice.order is not None and order is not None and invoice.order_id != order.pk:
        order = invoice.order
    if product is not None:
        add("صفحهٔ کالا", "قیمت اختصاصی، پله‌های قیمت، MOQ و فرم افزودن به سبد",
            product.get_absolute_url(), anon, True)
    add("سبد خرید (کاربر واردشده)", "قواعد فروش، مضرب بسته‌بندی، جمع سبد و فرم RFQ",
        reverse("shop:cart"), buyer)
    add("سبد خرید خالی", "حالت خالی با راهنمای بازگشت به فروشگاه", reverse("shop:cart"), anon)
    add("ثبت سفارش (Checkout)", "شمارهٔ PO، نشانی تحویل، روش پرداخت و اعتبار حساب",
        reverse("shop:checkout"), buyer)
    add("سفارش‌های من", "فهرست سفارش‌ها و صورت‌حساب‌ها با وضعیت‌های رنگی",
        reverse("shop:orders"), buyer)
    if order is not None:
        add("جزئیات سفارش", "اقلام، گردش سفارش و اطلاعات حمل",
            reverse("shop:order-detail", args=[order.number]), buyer)
    if invoice is not None:
        add("فاکتور / پیش‌فاکتور", "سند قابل چاپ با جمع‌ها و مانده", reverse("shop:invoice", args=[invoice.number]), buyer)
    payable = next((inv for inv in invoices if inv.balance > 0), None)
    if payable is not None:
        add("درگاه پرداخت (آزمایشی)", "تأیید پرداخت فاکتور با خلاصهٔ مبلغ و مانده",
            reverse("shop:invoice-pay", args=[payable.number]), buyer)
        add("پرداخت موفق", "تأیید ثبت پرداخت و وضعیت فاکتور",
            reverse("shop:payment-success", args=[payable.number]), buyer)
    add("ورود به حساب", "فرم ورود، بازیابی گذرواژه و مزایای حساب سازمانی", reverse("shop:login"), anon)
    add("ثبت‌نام شرکت", "فرم دو ستونی حساب کاربری و مشخصات شرکت", reverse("shop:signup"), anon)
    add("بازیابی گذرواژه", "مرحلهٔ درخواست پیوند بازیابی", reverse("shop:password-reset"), anon)
    add("پروفایل و آدرس‌ها", "ویرایش اطلاعات، افزودن/حذف نشانی", reverse("shop:profile"), buyer)
    add("دربارهٔ ما", "معرفی خطوط تولید و مزایای خرید", reverse("shop:about"), anon)
    add("تماس و پشتیبانی", "راه‌های تماس واحدهای فروش، فنی و مالی", reverse("shop:contact"), anon)

    sections = []
    for index, (title, note, url, client, full) in enumerate(pages, start=1):
        response = client.get(url, follow=True)
        html = response.content.decode("utf-8") if response.status_code == 200 else f"<p>خطا در رندر ({response.status_code})</p>"
        sections.append(f"""
<section class="pv-section" id="pv-{index}">
  <div class="pv-head">
    <span class="pv-num">{index}</span>
    <div><h2>{title}</h2><p>{note}</p></div>
    <code class="pv-url">{url}</code>
  </div>
  <div class="pv-frame">{clean(html, full=full)}</div>
</section>""")

    tokens = """
<section class="pv-section" id="pv-tokens">
  <div class="pv-head"><span class="pv-num">۰</span><div><h2>پالت رنگ و کنتراست</h2>
  <p>هر جفت رنگ متن/پس‌زمینه با معیار WCAG سنجیده شده است؛ نسبت‌ها در گزارش <code>docs/shop-theme-contrast.json</code> آمده‌اند.</p></div></div>
  <div class="pv-frame">
    <h3>رنگ‌های ساختاری</h3>
    <div class="pv-swatches">
      <div class="pv-swatch" style="background:var(--bg);color:var(--text)"><b>پس‌زمینهٔ صفحه</b><span>--bg</span></div>
      <div class="pv-swatch" style="background:var(--surface);color:var(--text)"><b>سطح کارت</b><span>--surface</span></div>
      <div class="pv-swatch" style="background:var(--surface-2);color:var(--text)"><b>سطح دوم</b><span>--surface-2</span></div>
      <div class="pv-swatch" style="background:var(--primary);color:#fff"><b>رنگ اصلی</b><span>--primary</span></div>
      <div class="pv-swatch" style="background:var(--primary-soft);color:var(--primary)"><b>رنگ اصلی ملایم</b><span>--primary-soft</span></div>
    </div>
    <h3>رنگ‌های وضعیت</h3>
    <div class="pv-swatches">
      <div class="pv-swatch" style="background:var(--ok-soft);color:var(--ok)"><b>موفق/موجود</b><span>--ok</span></div>
      <div class="pv-swatch" style="background:var(--warn-soft);color:var(--warn)"><b>هشدار/کمبود</b><span>--warn</span></div>
      <div class="pv-swatch" style="background:var(--danger-soft);color:var(--danger)"><b>خطا/منع</b><span>--danger</span></div>
      <div class="pv-swatch" style="background:var(--info-soft);color:var(--info)"><b>اطلاع</b><span>--info</span></div>
    </div>
    <h3>متن‌ها و نمونه‌های رابط</h3>
    <p>متن اصلی روی سطح کارت — <span class="text-muted">متن کم‌رنگ راهنما</span> — <a href="#">پیوند نمونه</a></p>
    <div class="row" style="gap:8px;flex-wrap:wrap">
      <button class="btn btn-primary">دکمهٔ اصلی</button>
      <button class="btn">دکمهٔ معمولی</button>
      <button class="btn btn-ghost">دکمهٔ کم‌رنگ</button>
      <button class="btn btn-danger">دکمهٔ حذف</button>
      <span class="badge badge-ok">موجود</span><span class="badge badge-warn">کمبود</span>
      <span class="badge badge-danger">ناموجود</span><span class="badge badge-info">پیشنهاد</span>
    </div>
    <div class="field" style="max-width:320px;margin-top:12px">
      <label for="pv-sample">نمونهٔ فیلد ورودی</label>
      <input id="pv-sample" class="form-input" value="FC-600">
      <span class="help">متن راهنمای زیر فیلد</span>
    </div>
    <div class="messages" style="margin-top:12px">
      <div class="alert alert-success"><span>نمونهٔ پیام موفقیت</span></div>
      <div class="alert alert-warning"><span>نمونهٔ پیام هشدار</span></div>
      <div class="alert alert-error"><span>نمونهٔ پیام خطا</span></div>
    </div>
  </div>
</section>"""

    nav = "\n".join(
        f'<a href="#pv-{i}">{i}. {t}</a>' for i, (t, _n, _u, _c, _f) in enumerate(pages, start=1))

    doc = f"""<!doctype html>
<html lang="fa" dir="rtl" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پیش‌نمایش سایت مشتری مهراصل — روشن و تیره</title>
<style>
{css_text()}
/* ---------- سبک خود پیش‌نمایش (بیرون از خود سایت) ---------- */
body {{ padding-bottom: 40px; }}
.pv-top {{
  position: sticky; top: 0; z-index: 60; background: var(--surface);
  border-bottom: 1px solid var(--border); padding: 10px 0; backdrop-filter: blur(6px);
}}
.pv-top .wrap {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
.pv-title {{ font-weight: 700; }}
.pv-nav {{ display: flex; gap: 4px; flex-wrap: wrap; max-height: 84px; overflow: auto; }}
.pv-nav a {{ font-size: 11.5px; padding: 3px 8px; border-radius: 999px; background: var(--surface-3); color: var(--text-2); }}
.pv-nav a:hover {{ background: var(--primary-soft); color: var(--primary); text-decoration: none; }}
.pv-section {{ margin-top: 26px; }}
.pv-head {{ display: flex; gap: 12px; align-items: baseline; margin-bottom: 8px; flex-wrap: wrap; }}
.pv-head h2 {{ margin: 0; font-size: 17px; }}
.pv-head p {{ margin: 0; color: var(--muted); font-size: 12.5px; }}
.pv-num {{ width: 24px; height: 24px; border-radius: 8px; background: var(--primary); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }}
.pv-url {{ margin-inline-start: auto; font-size: 11px; color: var(--muted); direction: ltr; }}
.pv-frame {{ border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--bg); }}
.pv-frame > .topbar, .pv-frame > .footer {{ position: static; }}
.pv-swatches {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; margin: 8px 0 16px; }}
.pv-swatch {{ border-radius: 12px; padding: 16px 14px; min-height: 86px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 4px; }}
.pv-swatch span {{ font-size: 11px; opacity: .85; direction: ltr; }}
[data-theme="dark"] .pv-swatch {{ border-color: var(--border-input); }}
</style>
</head>
<body>
<div class="pv-top">
  <div class="wrap">
    <span class="pv-title">پیش‌نمایش سایت مشتری مهراصل</span>
    <span class="text-sm text-muted">خروجی واقعی قالب‌ها از دیتابیس — بدون اینترنت هم کامل نمایش داده می‌شود</span>
    <span style="flex:1"></span>
    <a class="btn btn-sm" href="#pv-tokens">پالت رنگ</a>
    <button class="btn btn-sm btn-primary theme-toggle" type="button" data-theme-toggle>
      <span class="on-light">حالت تیره</span><span class="on-dark">حالت روشن</span>
    </button>
  </div>
  <div class="wrap"><nav class="pv-nav">{nav}</nav></div>
</div>

<div class="wrap">
{tokens}
{''.join(sections)}
  <p class="text-sm text-muted" style="margin-top:20px">
    این فایل یک تصویر ایستا از صفحه‌های واقعی سایت است؛ فرم‌ها و پیوندها در پیش‌نمایش غیرفعال‌اند.
    برای تجربهٔ کامل: <code>PANEL_DEMO_AUTOLOGIN=0 python3 manage.py runserver 0.0.0.0:8000</code>
  </p>
</div>

<script>
/* کلید تم پیش‌نمایش — همان منطق سایت با پشتیبان خطا (محیط sandbox بدون localStorage) */
(function () {{
  var KEY = "mehrasl-shop-theme";
  function get() {{ try {{ return localStorage.getItem(KEY); }} catch (e) {{ return null; }} }}
  function set(v) {{ try {{ localStorage.setItem(KEY, v); }} catch (e) {{}} }}
  function apply(t) {{
    document.documentElement.setAttribute("data-theme", t);
  }}
  apply(get() || (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {{
    b.addEventListener("click", function () {{
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      set(next); apply(next);
    }});
  }});
}})();
</script>
</body>
</html>"""
    OUT.write_text(doc, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"پیش‌نمایش ساخته شد: {path}  ({path.stat().st_size / 1024:.0f} کیلوبایت)")
