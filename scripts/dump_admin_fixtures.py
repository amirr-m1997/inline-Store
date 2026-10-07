"""ذخیره‌ی HTML صفحه‌های واقعی پنل برای تست آفلاین (DOM) در scripts/check_panel_dom.js

اجرا:
    cd /home/user/mehrasl-panel
    python3 scripts/dump_admin_fixtures.py /tmp/admin_fixtures
"""
from __future__ import annotations

import os
import pathlib
import sys

import django

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

PAGES = {
    "orders_changelist": "/admin/orders/order/",
    "orders_filtered": "/admin/orders/order/?ordered_at_from=1405/07/01&ordered_at_to=1405/07/15",
    "product_changelist": "/admin/catalog/product/",
    "invoice_change": None,  # پر می‌شود: اولین فاکتور
    "dashboard": "/admin/",
    "login": "/admin/login/",
}


def main(out_dir: str) -> None:
    target = pathlib.Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    user = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    c = Client()
    c.force_login(user)
    anon = Client()

    from finance.models import Invoice

    invoice = Invoice.objects.order_by("-id").first()
    PAGES["invoice_change"] = f"/admin/finance/invoice/{invoice.pk}/change/"

    for name, url in PAGES.items():
        client = anon if name == "login" else c
        html = client.get(url).content.decode()
        (target / f"{name}.html").write_text(html, encoding="utf-8")
        print(f"✓ {name:22s} {url:60s} {len(html):>7,d} بایت")

    print(f"\nمقصد: {target}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/admin_fixtures")
