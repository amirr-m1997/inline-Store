"""ساخت پیش‌نمایش تک‌فایلی «روشن/تیره» از پنل واقعی (با دادهٔ db.sqlite3).

چرا؟ برای بازبینی دستهٔ «مشتری سخت‌گیر» باید همان صفحه‌ها در هر دو تم کنار هم دیده شوند.
این اسکریپت:
  ۱. صفحه‌های واقعی را با کلاینت آزمایشی جنگو از پایگاه‌داده می‌خواند،
  ۲. panel.js را با jsdom روی همان HTML اجرا می‌کند (تا کنش‌های درون‌ردیفی و
     پیوند «پرش به محتوا» هم در پیش‌نمایش دیده شوند — همان خروجی مرورگر)،
  ۳. CSS و فونت‌ها را درون فایل جای می‌دهد (بدون شبکه، بدون CDN) و هر صفحه را
     دو بار می‌چیند: یک‌بار روشن، یک‌بار تیره.

اجرا:
    python3 scripts/build_panel_theme_preview.py [--out /home/user/mehrasl-panel-theme-preview.html]
"""
from __future__ import annotations

import argparse
import os
import re
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

import build_static_preview as bsp  # noqa: E402

PAGES = [
    ("داشبورد عملیاتی", "KPI، نمودار فروش، قیف، کارتابل‌ها و هشدارها", "/admin/"),
    ("مرکز اعلان‌ها", "فهرست اعلان‌ها با فیلتر شدت/نوع/وضعیت", "/admin/alerts/"),
    ("گزارش‌ساز", "گزارش با بُعدهای مختلف و خروجی اکسل", "/admin/reports/"),
    ("سفارش سریع", "چسباندن فهرست کد کالا و تبدیل به سفارش", "/admin/quick-order/"),
    ("فهرست سفارش‌ها (ناحیهٔ فهرست)",
     "کنش‌های درون‌ردیفی، نوار راهنمای فهرست و میان‌بر جست‌وجو — این ناحیه را "
     "خود جنگو/Tailwind می‌چیند و panel.css فقط بخش‌های اختصاصی را روی آن می‌گذارد",
     "/admin/orders/order/"),
]


def enhanced_html(client, url: str, tmpdir: pathlib.Path) -> str:
    """HTML صفحه + اجرای panel.js روی آن (خروجی DOM مرورگر)."""
    src = tmpdir / "in"
    dst = tmpdir / "out"
    src.mkdir(parents=True, exist_ok=True)
    (src / "page.html").write_text(client.get(url).content.decode(), encoding="utf-8")
    env = dict(os.environ, NODE_PATH="/tmp/jsd/node_modules")
    proc = subprocess.run(
        ["node", str(ROOT / "scripts/render_panel_with_js.js"), str(src), str(dst)],
        capture_output=True, text=True, env=env, check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr)
        raise SystemExit("اجرای jsdom ناموفق بود")
    print(f"   {proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ''}")
    return (dst / "page.html").read_text(encoding="utf-8")


def extract_by_marker(html: str, marker: str, tag: str) -> str | None:
    """استخراج یک بلوک با تطبیق عمق تگ (برای صفحه‌هایی که panel-wrap ندارند)."""
    start = html.find(marker)
    if start == -1:
        return None
    depth = 0
    token = re.compile(rf"<{tag}\b|</{tag}>")
    index = start
    while True:
        match = token.search(html, index)
        if not match:
            return None
        if match.group(0).startswith(f"<{tag}"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return html[start:match.end()]
        index = match.end()


def block_of(html: str) -> str:
    try:
        block = bsp.extract_panel_block(html)
    except SystemExit:
        # فهرست‌های جنگو panel-wrap ندارند؛ ناحیهٔ فهرست را جدا می‌کنیم
        block = extract_by_marker(html, '<form id="changelist-form"', "form") or ""
    block = bsp.replace_icons(block)
    block = bsp.strip_scripts(block)
    return block


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="/home/user/mehrasl-panel-theme-preview.html")
    options = parser.parse_args()

    css = (ROOT / "static/css/panel.css").read_text(encoding="utf-8")
    for name in ("Regular", "Medium", "SemiBold", "Bold"):
        uri = bsp.font_data_uri(ROOT / "static/fonts" / f"Vazirmatn-{name}.woff2")
        css = css.replace(f'url("/static/fonts/Vazirmatn-{name}.woff2")', f"url({uri})")

    client = bsp.make_client()
    sections = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        for title, note, url in PAGES:
            html = enhanced_html(client, url, tmpdir)
            sections.append((title, note, block_of(html)))

    body = []
    for title, note, block in sections:
        body.append(f"""
  <section class="pv-page">
    <header class="pv-page-head">
      <h2>{title}</h2>
      <p>{note} — داده‌ها از <code>db.sqlite3</code> واقعی خوانده شده‌اند.</p>
    </header>
    <div class="pv-pair">
      <div class="pv-theme pv-light">
        <span class="pv-tag">تم روشن</span>
        <div class="panel-wrap">{block}</div>
      </div>
      <div class="pv-theme dark">
        <span class="pv-tag">تم تیره</span>
        <div class="panel-wrap">{block}</div>
      </div>
    </div>
  </section>""")

    document = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>پنل مهراصل — پیش‌نمایش روشن/تیره (دادهٔ واقعی)</title>
<style>
{css}

/* ---------------------------------------------------------- پوستهٔ پیش‌نمایش */
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: #eef2f8; color: #0f1b2d;
  font-family: "Vazirmatn", "IRANSansX", Tahoma, system-ui, sans-serif;
}}
.pv-shell {{ max-width: 1560px; margin: 0 auto; padding: 22px 18px 60px; }}
.pv-hero {{
  background: linear-gradient(135deg, #0d1a2b, #0e7490);
  color: #fff; border-radius: 18px; padding: 20px 22px; margin-bottom: 22px;
}}
.pv-hero h1 {{ margin: 0 0 6px; font-size: 20px; }}
.pv-hero p {{ margin: 0; font-size: 13px; line-height: 2; color: #d7ecf3; }}
.pv-hero b {{ color: #fff; }}
.pv-note {{ font-size: 12.5px; line-height: 2; color: #d7ecf3; margin-top: 8px; }}
.pv-page {{ margin-bottom: 30px; }}
.pv-page-head h2 {{ margin: 0 0 4px; font-size: 16px; color: #0d1a2b; }}
.pv-page-head p {{ margin: 0 0 12px; font-size: 12.5px; color: #55637a; }}
.pv-pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }}
@media (max-width: 1200px) {{ .pv-pair {{ grid-template-columns: 1fr; }} }}
.pv-theme {{
  position: relative; border-radius: 16px; padding: 16px 14px 8px;
  border: 1px solid #dbe3ef; background: #fff; overflow: hidden;
}}
.pv-theme.dark {{ background: #0b1626; border-color: #1b2a40; }}
.pv-tag {{
  position: absolute; top: 10px; inset-inline-start: 12px; font-size: 11px;
  padding: 2px 9px; border-radius: 999px; background: #e8f4f8; color: #0e7490;
}}
.pv-theme.dark .pv-tag {{ background: #123047; color: #3ec3dd; }}
.pv-foot {{ margin-top: 26px; font-size: 12px; color: #55637a; line-height: 2; }}
</style>
</head>
<body>
<div class="pv-shell">
  <div class="pv-hero">
    <h1>پنل مدیریت مهراصل — پیش‌نمایش همان‌صفحه در دو تم</h1>
    <p>
      این فایل از <b>پایگاه‌دادهٔ واقعی پروژه</b> ساخته شده است؛ هیچ محتوایی دستی نوشته نشده.
      HTML هر صفحه از سرور جنگو گرفته می‌شود و سپس <b>panel.js</b> روی آن اجرا می‌شود
      (با jsdom) تا کنش‌های درون‌ردیفی، نوار راهنمای فهرست، پیوند «پرش به محتوای اصلی» و
      میان‌بر جست‌وجو هم — دقیقاً مثل مرورگر — دیده شوند.
    </p>
    <p class="pv-note">
      فونت وزیرمتن و همهٔ استایل‌ها درون همین فایل جای گرفته‌اند؛ بدون اینترنت و بدون CDN باز می‌شود.
      رنگ‌ها از توکن‌های <code>--panel-*</code> می‌آیند و کنتراست هر دو تم سنجیده شده است
      (<code>scripts/panel_ux_audit.py</code>).
    </p>
  </div>
{''.join(body)}

  <p class="pv-foot">
    نکته: در تم تیره، کلاس <code>dark</code> (همان کاری که دکمهٔ تم پنل انجام می‌دهد) روی ظرف صفحه
    گذاشته شده است؛ بنابراین همان قواعد CSS پنل اجرا می‌شوند و هیچ استایل جداگانه‌ای برای پیش‌نمایش
    نوشته نشده. برای مقایسهٔ ستون‌به‌ستون، دو تم کنار هم چیده شده‌اند.
  </p>
</div>
</body>
</html>
"""
    out = pathlib.Path(options.out)
    out.write_text(document, encoding="utf-8")
    print(f"\nپیش‌نمایش ساخته شد: {out} ({out.stat().st_size / 1024:.0f} کیلوبایت)")


if __name__ == "__main__":
    main()
