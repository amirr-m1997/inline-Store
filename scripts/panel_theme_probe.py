"""کاوش دقیق UI پنل: کنتراست متن در بافت، ارقام لاتین، یکدستی قلم، تراز و RTL.

اجرا:  PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers python3 scripts/panel_theme_probe.py
خروجی: docs/panel-theme-probe.json + چاپ خلاصه در ترمینال
"""
from __future__ import annotations

import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("PANEL_BASE", "http://127.0.0.1:8000")
PAGES = [
    ("داشبورد", "/admin/"),
    ("سفارش‌ها", "/admin/orders/order/"),
    ("فاکتور", "/admin/finance/invoice/1/change/"),
    ("اعلان‌ها", "/admin/alerts/"),
    ("گزارش‌ها", "/admin/reports/"),
    ("سفارش سریع", "/admin/quick-order/"),
]
PROBE = r"""() => {
  /* تبدیل هر رنگ محاسبه‌شده (rgb/oklch/color-mix) به RGBA با بوم مرورگر */
  const cvs = document.createElement("canvas"); cvs.width = cvs.height = 1;
  const cx = cvs.getContext("2d", {willReadFrequently: true});
  const parse = (c) => {
    if (!c || c === "transparent" || c === "rgba(0, 0, 0, 0)") return null;
    const m = (c || "").match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
    if (m) return [ +m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4] ];
    try {
      cx.clearRect(0, 0, 1, 1); cx.fillStyle = "#000";
      cx.fillStyle = c;
      if (cx.fillStyle === "#000" && !/^#000/.test(c)) return null;
      cx.fillRect(0, 0, 1, 1);
      const d = cx.getImageData(0, 0, 1, 1).data;
      return [d[0], d[1], d[2], d[3] / 255];
    } catch (e) { return null; }
  };
  const lum = ([r, g, b]) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (fg, bg) => {
    const [l1, l2] = [lum(fg), lum(bg)].sort((a, b) => b - a);
    return (l1 + 0.05) / (l2 + 0.05);
  };
  const blend = (top, bottom) => {
    const a = top[3];
    return [0, 1, 2].map((i) => Math.round(top[i] * a + bottom[i] * (1 - a)));
  };
  const effectiveBg = (el) => {
    let bg = [255, 255, 255, 1];
    const stack = [];
    let n = el;
    while (n && n.nodeType === 1) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c[3] > 0) stack.push(c);
      n = n.parentElement;
    }
    stack.reverse().forEach((c) => { bg = c[3] === 1 ? c.slice(0, 3) : blend(c, bg); });
    return bg;
  };
  const path = (el) => {
    const parts = []; let node = el;
    for (let i = 0; i < 4 && node && node.nodeType === 1; i++) {
      let s = node.tagName.toLowerCase();
      if (node.id) s += "#" + node.id;
      else if (node.classList.length) s += "." + [...node.classList].slice(0, 2).join(".");
      parts.unshift(s); node = node.parentElement;
    }
    return parts.join(" > ");
  };
  const out = {contrast: [], latinDigits: [], fonts: {}, justify: [], letterSpacing: [], svgText: 0};
  const isCode = (el) => !!el.closest("code, pre, input, textarea, select, [dir=ltr], .bidi-ltr, .model-help code");

  document.querySelectorAll("body *").forEach((el) => {
    if (el.children.length > 0) return;
    const text = (el.textContent || "").trim();
    const r = el.getBoundingClientRect();
    if (!text || r.width < 4 || r.height < 4) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden" || cs.display === "none") return;

    /* ۱) کنتراست متن در بافت واقعی */
    const fg = parse(cs.color);
    if (fg) {
      const bg = effectiveBg(el);
      const cr = ratio(fg.slice(0, 3), bg);
      const size = parseFloat(cs.fontSize);
      const bold = (parseInt(cs.fontWeight, 10) || 400) >= 600;
      const large = size >= 18.66 || (size >= 14 && bold);
      /* آیکون‌های فونت‌ی نماد هستند، نه متن (WCAG 1.4.11 → کمینه ۳:۱) */
      const icon = el.classList.contains("material-symbols-outlined");
      const min = icon ? 3 : (large ? 3 : 4.5);
      if (cr < min) {
        out.contrast.push({el: path(el), ratio: Math.round(cr * 100) / 100, min, size,
                           text: text.slice(0, 28)});
      }
    }
    /* ۲) ارقام لاتین در متن فارسی */
    if (!isCode(el) && /[0-9]/.test(text) && /[\u0600-\u06FF]/.test(text)) {
      out.latinDigits.push({el: path(el), text: text.slice(0, 32)});
    }
    /* ۳) یکدستی قلم */
    const size = parseFloat(cs.fontSize);
    const key = String(Math.round(size * 10) / 10);
    out.fonts[key] = (out.fonts[key] || 0) + 1;
    /* ۴) تراز و فاصلهٔ حروف (ناسازگار با فارسی) */
    if (cs.textAlign === "justify") out.justify.push({el: path(el), text: text.slice(0, 24)});
    if (cs.letterSpacing && cs.letterSpacing !== "normal") {
      out.letterSpacing.push({el: path(el), ls: cs.letterSpacing, text: text.slice(0, 24)});
    }
  });
  out.svgText = document.querySelectorAll("svg text").length;
  return out;
}"""


def main() -> int:
    report: dict = {"pages": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for theme in ("light", "dark"):
            for width in (390, 1440):
                ctx = browser.new_context(viewport={"width": width, "height": 900})
                pg = ctx.new_page()
                pg.add_init_script(f"localStorage.setItem('theme','{theme}');"
                                   f"document.documentElement.classList.toggle('dark', {str(theme == 'dark').lower()});")
                for name, path in PAGES:
                    pg.goto(BASE + path, wait_until="networkidle")
                    pg.wait_for_timeout(250)
                    data = pg.evaluate(PROBE)
                    data["theme"], data["width"] = theme, width
                    report["pages"][f"{name}|{theme}|{width}"] = data
                    flags = len(data["contrast"]) + len(data["latinDigits"]) + len(data["justify"])
                    print(f"— {name} | {theme} | {width}px → کنتراستِ کم: {len(data['contrast'])}"
                          f" | ارقام لاتین: {len(data['latinDigits'])} | justify: {len(data['justify'])}"
                          f" | فونت‌ها: {sorted(data['fonts'])}")
                ctx.close()
        browser.close()
    os.makedirs("docs", exist_ok=True)
    with open("docs/panel-theme-probe.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("گزارش JSON: docs/panel-theme-probe.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
