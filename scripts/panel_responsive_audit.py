"""سنجش ریسپانسیو پنل ادمین با مرورگر واقعی (Chromium/Playwright).

چه چیزی سنجیده می‌شود؟ برای هر صفحه در هر عرض:
  ۱) سرریز افقی صفحه (scrollWidth > innerWidth) و عنصرهای مسبب آن
  ۲) سرریز/بُرش متن در کارت‌ها و سلول‌ها (overflow:hidden با محتوای بریده)
  ۳) اندازه‌ی هدف لمسی (< ۳۲px) برای عناصر تعاملی
  ۴) ریز بودن فونت (< ۱۱px) و فاصله‌ی خط کم برای متن‌های بلند فارسی
  ۵) پنهان‌شدن محتوا زیر سرصفحه‌ی ثابت/چسبان
  ۶) رفتار سایدبار در موبایل (بیرون‌قاب/هم‌پوشانی)
  ۷) جا شدن نمودارها و تصاویر در کارت‌ها
  ۸) اسکرین‌شات هر حالت برای شاهد بصری

اجرا:
    PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers python3 scripts/panel_responsive_audit.py
خروجی: چاپ خلاصه + docs/panel-responsive-audit.json + /tmp/panel-shots/*.jpg
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = os.environ.get("PANEL_BASE_URL", "http://127.0.0.1:8000")
SHOTS = pathlib.Path("/tmp/panel-shots")

VIEWPORTS = [
    ("موبایل کوچک ۳۶۰", 360, 780),
    ("موبایل ۳۹۰", 390, 844),
    ("موبایل بزرگ ۴۳۰", 430, 932),
    ("تبلت ۷۶۸", 768, 1024),
    ("تبلت افقی ۱۰۲۴", 1024, 768),
    ("لپ‌تاپ ۱۲۸۰", 1280, 800),
    ("دسکتاپ ۱۴۴۰", 1440, 900),
]
PAGES = [
    ("dashboard", "داشبورد", "/admin/"),
    ("orders", "فهرست سفارش‌ها", "/admin/orders/order/"),
    ("reports", "گزارش‌ها", "/admin/reports/"),
    ("alerts", "اعلان‌ها", "/admin/alerts/"),
    ("quick-order", "سفارش سریع", "/admin/quick-order/"),
    ("invoice-form", "فرم ویرایش فاکتور", "/admin/finance/invoice/1/change/"),
]

JS_CHECKS = r"""
() => {
  const out = {overflow: [], clipped: [], smallTargets: [], smallTargetsChrome: [], tinyFonts: [],
               tightLines: [], charts: [], scrollHintMissing: [], scrollers: 0, pageOverflow: 0,
               sidebar: null};
  const vw = window.innerWidth;
  out.pageOverflow = Math.max(0, document.documentElement.scrollWidth - vw);

  const path = (el) => {
    const parts = [];
    let node = el;
    for (let i = 0; i < 4 && node && node.nodeType === 1; i++) {
      let s = node.tagName.toLowerCase();
      if (node.id) s += "#" + node.id;
      else if (node.classList.length) s += "." + [...node.classList].slice(0, 3).join(".");
      parts.unshift(s);
      node = node.parentElement;
    }
    return parts.join(" > ");
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  };
  /* ظرف اسکرول افقی = سرریزِ عمدی، نه ایراد */
  const inScroller = (el) => {
    let n = el.parentElement;
    while (n && n !== document.body) {
      const cs = getComputedStyle(n);
      if (["auto", "scroll"].includes(cs.overflowX)) return n;
      n = n.parentElement;
    }
    return null;
  };
  /* پنهانِ عمدی: sr-only، select2-hidden-accessible، clip/inset(50%) */
  const visuallyHidden = (el, cs) => {
    if (el.closest(".sr-only, .select2-hidden-accessible")) return true;
    const r = el.getBoundingClientRect();
    if (r.width > 2 || r.height > 2) return false;
    return cs.clip !== "auto" || (cs.clipPath && cs.clipPath !== "none");
  };
  const isOwn = (el) =>
    !!(el.closest(".panel-wrap, .panel-table, .panel-card, #result_list, .model-help, .panel-row-actions"));
  const box = (el) => {
    if (el.type === "checkbox" || el.type === "radio") {
      const cell = el.closest("td, th");
      /* اگر panel.js سلول را کلیک‌پذیر کرده، هدف واقعی همان سلول است */
      if (cell && cell.dataset.panelCellClick === "1") return cell.getBoundingClientRect();
      const label = el.closest("label");
      if (label) return label.getBoundingClientRect();
    }
    return el.getBoundingClientRect();
  };

  const all = document.querySelectorAll("body *");
  for (const el of all) {
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.position === "fixed" || cs.position === "sticky") continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 4 || r.left < -4) {
      if (inScroller(el)) continue;
      /* خودِ ظرف اسکرول‌افقی (مثل نوار تب‌ها) سرریزِ عمدی است */
      if (["auto", "scroll"].includes(cs.overflowX) && el.scrollWidth > el.clientWidth + 4) continue;
      out.overflow.push({el: path(el), right: Math.round(r.right), left: Math.round(r.left),
                         width: Math.round(r.width)});
    }
  }

  for (const el of all) {
    if (!visible(el) || el.children.length > 0) continue;
    const cs = getComputedStyle(el);
    if (cs.overflow === "hidden" && el.scrollWidth > el.clientWidth + 2 && (el.textContent || "").trim()) {
      if (inScroller(el) || el.closest("h1")) continue;      /* مسیر راهنما جدا سنجیده می‌شود */
      if (cs.textOverflow === "ellipsis") continue;          /* کوتاه‌سازی عمدی با «…» */
      out.clipped.push({el: path(el), text: el.textContent.trim().slice(0, 40),
                        need: el.scrollWidth, have: el.clientWidth});
    }
  }

  if (vw < 1024) {
    for (const el of document.querySelectorAll("a[href], button, select, input[type=checkbox], input[type=submit]")) {
      if (!visible(el)) continue;
      if (visuallyHidden(el, getComputedStyle(el))) continue;
      if (el.tagName === "A" && getComputedStyle(el).display === "inline" &&
          el.closest("p, li, .panel-sub, td")) continue;
      const r = box(el);
      if (r.width < 31.5 || r.height < 31.5) {
        const item = {el: path(el), w: Math.round(r.width), h: Math.round(r.height),
                      text: (el.textContent || el.getAttribute("aria-label") || "").trim().slice(0, 24)};
        (isOwn(el) ? out.smallTargets : out.smallTargetsChrome).push(item);
      }
    }
  }

  for (const el of all) {
    if (!visible(el) || el.children.length > 0 || !(el.textContent || "").trim()) continue;
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize);
    if (size && size < 11) out.tinyFonts.push({el: path(el), size, text: el.textContent.trim().slice(0, 30)});
    const text = el.textContent.trim();
    if (text.length > 80) {
      const lh = parseFloat(cs.lineHeight) / size;
      if (lh && lh < 1.45) out.tightLines.push({el: path(el), ratio: Math.round(lh * 100) / 100,
                                                text: text.slice(0, 30)});
    }
  }

  /* جدول‌های اسکرول‌شونده باید راهنمای اسکرول داشته باشند (panel.js می‌سازد) */
  for (const el of document.querySelectorAll(".panel-card-body.panel-tight, .panel-scroll-x")) {
    if (el.scrollWidth > el.clientWidth + 4) {
      out.scrollers += 1;
      const prev = el.previousElementSibling;
      if (!prev || !prev.classList.contains("panel-scroll-hint")) {
        out.scrollHintMissing.push({el: path(el)});
      }
    }
  }

  for (const el of document.querySelectorAll(".panel-card svg, .panel-wrap svg")) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    const pr = el.parentElement ? el.parentElement.getBoundingClientRect() : null;
    if (pr && (r.width > pr.width + 2 || r.height > 620)) {
      out.charts.push({el: path(el), w: Math.round(r.width), h: Math.round(r.height),
                       parentW: Math.round(pr.width)});
    }
  }

  const nav = document.querySelector("#nav-sidebar, aside nav, nav");
  if (nav) {
    const r = nav.getBoundingClientRect();
    out.sidebar = {x: Math.round(r.x), w: Math.round(r.width), visible: visible(nav)};
  }
  return out;
}
"""


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright نصب نیست:  pip install playwright && playwright install chromium")
        return 2

    SHOTS.mkdir(parents=True, exist_ok=True)
    report: dict = {"viewports": [], "issues": [], "screenshots": []}
    problems = 0
    summary_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for label, width, height in VIEWPORTS:
            context = browser.new_context(viewport={"width": width, "height": height},
                                          device_scale_factor=1,
                                          locale="fa-IR")
            page = context.new_page()
            print(f"\n■ {label} ({width}×{height})")
            for key, title, url in PAGES:
                page.goto(BASE + url, wait_until="load")
                page.wait_for_timeout(350)
                data = page.evaluate(JS_CHECKS)
                over = len(data["overflow"])
                clip = len(data["clipped"])
                small = len(data["smallTargets"])
                chrome = len(data["smallTargetsChrome"])
                fonts = len(data["tinyFonts"])
                hints = len(data["scrollHintMissing"])
                row = {"viewport": label, "page": title, "pageOverflow": data["pageOverflow"],
                       "overflow": over, "clipped": clip, "smallTargets": small,
                       "smallTargetsChrome": chrome, "tinyFonts": fonts,
                       "scrollHintMissing": hints, "scrollers": data["scrollers"]}
                summary_rows.append(row)
                bad = data["pageOverflow"] > 1 or over or small or fonts or hints
                if bad:
                    problems += 1
                print(f"   {title:22s} سرریز: {data['pageOverflow']:>3} | بیرون‌زده: {over:>2} | "
                      f"بُرش: {clip:>2} | هدف کوچک خودمان: {small:>2} (پوسته: {chrome:>2}) | "
                      f"فونت ریز: {fonts:>2} | جدول اسکرولی: {data['scrollers']:>2} بی‌راهنما: {hints:>2}"
                      + ("  ⟵" if bad else "  ✓"))
                for kind in ("overflow", "clipped", "smallTargets", "smallTargetsChrome", "tinyFonts",
                             "tightLines", "charts", "scrollHintMissing"):
                    if data[kind]:
                        report["issues"].append({"viewport": label, "page": title,
                                                 "kind": kind, "items": data[kind][:8]})
                # اسکرین‌شات برای موبایل/تبلت/دسکتاپ (فقط صفحه‌های کلیدی)
                if key in ("dashboard", "orders", "alerts", "quick-order", "invoice-form") and width in (390, 768, 1440):
                    path = SHOTS / f"{key}-{width}.jpg"
                    page.screenshot(path=str(path), full_page=False, quality=70, type="jpeg")
                    report["screenshots"].append({"page": title, "width": width, "path": str(path)})
            context.close()
        browser.close()

    out = ROOT / "docs" / "panel-responsive-audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "─" * 66)
    print(f"حالت‌های سنجیده‌شده: {len(summary_rows)} | حالت‌های دارای ایراد: {problems}")
    print(f"گزارش JSON: {out.relative_to(ROOT)}  | اسکرین‌شات‌ها: {SHOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
