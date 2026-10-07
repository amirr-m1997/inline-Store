"""اسکرین‌شات پنل ادمین در دو تم (روشن/تیره) و چند عرض — برای بازبینی چشمی UI.

استفاده:  PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers python3 scripts/panel_ui_shots.py
خروجی:   /tmp/panel-ui/<page>-<width>-<theme>.jpg
"""
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("PANEL_BASE", "http://127.0.0.1:8000")
OUT = os.environ.get("PANEL_UI_OUT", "/tmp/panel-ui")
PAGES = [
    ("dashboard", "/admin/"),
    ("orders", "/admin/orders/order/"),
    ("invoice-form", "/admin/finance/invoice/1/change/"),
    ("alerts", "/admin/alerts/"),
    ("reports", "/admin/reports/"),
    ("quick-order", "/admin/quick-order/"),
]
WIDTHS = [390, 1440]


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width in WIDTHS:
            for theme in ("light", "dark"):
                ctx = browser.new_context(viewport={"width": width, "height": 900},
                                          device_scale_factor=1)
                pg = ctx.new_page()
                pg.add_init_script(f"localStorage.setItem('theme','{theme}');"
                                   f"document.documentElement.classList.toggle('dark', {str(theme == 'dark').lower()});")
                for name, path in PAGES:
                    pg.goto(BASE + path, wait_until="networkidle")
                    pg.wait_for_timeout(400)
                    pg.screenshot(path=f"{OUT}/{name}-{width}-{theme}.jpg", full_page=True,
                                  type="jpeg", quality=72)
                    print("✓", f"{name}-{width}-{theme}.jpg")
                ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
