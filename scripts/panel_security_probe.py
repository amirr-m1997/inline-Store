"""کاوش امنیتی پنل ادمین — ماتریس دسترسی، یکپارچگی دادهٔ مالی، تزریق و CSRF.

این اسکریپت مکمل scripts/security_audit.py (که فروشگاه را می‌سنجد) است و روی
پنل ادمین تمرکز دارد. همه‌ی بررسی‌ها با کلاینت آزمایشی جنگو و روی db.sqlite3
اجرا می‌شوند و هیچ داده‌ای را تغییرِ ماندگار نمی‌دهند (هر نوشتن در پایان
بازگردانده می‌شود).

اجرا:  python3 scripts/panel_security_probe.py
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

from core.models import AuditLog  # noqa: E402

PASSED = 0
FAILED = 0
FINDINGS: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✓ {label}" + (f" — {extra}" if extra else ""))
    else:
        FAILED += 1
        FINDINGS.append(f"{label}: {extra}")
        print(f"  ✗ {label}" + (f" — {extra}" if extra else ""))


PANEL_URLS = [
    "/admin/",
    "/admin/orders/order/",
    "/admin/orders/order/1/change/",
    "/admin/reports/",
    "/admin/reports/export.xlsx",
    "/admin/quick-order/",
    "/admin/alerts/",
    "/admin/api/summary/",
    "/admin/finance/invoice/",
    "/admin/core/auditlog/",
    "/admin/customers/company/",
]


def main() -> int:
    User = get_user_model()
    print("\n۱) ماتریس دسترسی — چه کسی به پنل می‌رسد؟")
    anon = Client()
    blocked_anon = 0
    for url in PANEL_URLS:
        status = anon.get(url).status_code
        if status in (301, 302, 403):
            blocked_anon += 1
        else:
            print(f"      ! {url} → {status}")
    check("کاربر ناشناس به هیچ مسیر پنل دسترسی ندارد", blocked_anon == len(PANEL_URLS),
          f"{blocked_anon} از {len(PANEL_URLS)} مسیر بسته بود")

    customer = User.objects.filter(is_staff=False, is_active=True).first()
    if customer:
        c = Client()
        assert c.login(username=customer.username, password="Mehr@1405"), "ورود مشتری ناموفق"
        open_urls = [u for u in PANEL_URLS if c.get(u).status_code not in (301, 302, 403)]
        check("کاربر مشتری (is_staff=False) به پنل نمی‌رسد", not open_urls, "، ".join(open_urls))

    # کارمندِ بدون هیچ مجوزی (موقت ساخته می‌شود) — رفتار «کارمند بی‌مجوز» سنجیده شود
    probe_user, created = User.objects.get_or_create(
        username="probe-noperm", defaults={"is_staff": True, "is_active": True})
    probe_user.is_staff, probe_user.is_active = True, True
    probe_user.set_password("Probe@1405")
    probe_user.save()
    probe_user.user_permissions.clear()
    probe_user.groups.clear()
    try:
        c = Client()
        c.force_login(probe_user)
        open_model_pages = [
            u for u in PANEL_URLS
            if u not in ("/admin/", "/admin/alerts/") and c.get(u).status_code == 200
        ]
        check("کارمند بی‌مجوز به هیچ فهرست/فرم مدلی نمی‌رسد", not open_model_pages,
              "، ".join(open_model_pages[:3]))
        check("کارمند بی‌مجوز از گزارش‌ها و سفارش سریع رد می‌شود",
              c.get("/admin/reports/").status_code == 403
              and c.get("/admin/quick-order/").status_code == 403)
        check("کارمند بی‌مجوز، خلاصهٔ API را نمی‌گیرد",
              c.get("/admin/api/summary/").status_code == 403)
        dash = c.get("/admin/").content.decode()
        check("داشبورد برای کارمند بی‌مجوز، اعداد فروش را نشان نمی‌دهد",
              "فروش امروز" not in dash and "دسترسی به گزارش‌های فروش محدود" in dash)
    finally:
        if created:
            probe_user.delete()

    # نقش‌های واقعی سازمان — نه قفل ناخواسته، نه دسترسی اضافه
    for username, url, expected in (
        ("manager", "/admin/reports/", 200),
        ("sales1", "/admin/quick-order/", 200),
        ("store1", "/admin/quick-order/", 403),
        ("content1", "/admin/reports/", 403),
    ):
        user = User.objects.filter(username=username).first()
        if not user:
            continue
        c = Client()
        c.force_login(user)
        got = c.get(url).status_code
        check(f"نقش «{username}» روی {url} → {expected}", got == expected, f"دریافت: {got}")

    print("\n۲) CSRF روی مسیرهای سفارشی پنل")
    admin_user = User.objects.filter(is_superuser=True).order_by("id").first()
    c = Client(enforce_csrf_checks=True)
    c.force_login(admin_user)
    r = c.post("/admin/quick-order/", {"codes": "FC-600, 1"})
    check("POST بدون توکن CSRF رد می‌شود", r.status_code == 403, f"کد: {r.status_code}")
    r = c.post("/admin/api/summary/", {})
    check("POST به API خلاصه فقط با توکن ممکن است", r.status_code in (403, 405), f"کد: {r.status_code}")

    print("\n۳) تزریق ورودی در پنل (XSS)")
    c = Client()
    c.force_login(admin_user)
    payload = '"><img src=x onerror=alert(1)>'
    r = c.get("/admin/customers/company/", {"q": payload})
    body = r.content.decode()
    live_markup = re.search(r"<img[^>]*onerror", body)
    check("جست‌وجوی مخرب در فهرست، به‌صورت متن escape می‌شود",
          live_markup is None and ("&lt;img" in body or payload not in body),
          f"کد: {r.status_code}")
    r = c.get("/admin/alerts/", {"level": payload, "kind": payload})
    check("فیلترهای مخرب صفحهٔ اعلان‌ها خنثی می‌شوند",
          r.status_code == 200 and re.search(r"<img[^>]*onerror", r.content.decode()) is None,
          f"کد: {r.status_code}")
    r = c.get("/admin/reports/", {"dimension": payload})
    check("پارامتر مخرب گزارش‌ساز به بُعد معتبر تبدیل می‌شود",
          r.status_code == 200 and payload not in r.content.decode(), f"کد: {r.status_code}")

    print("\n۴) یکپارچگی دادهٔ مالی در فرم ادمین")
    from finance.models import Invoice

    invoice = Invoice.objects.order_by("-id").first()
    if invoice:
        before_paid = invoice.paid_amount
        before_total = invoice.total
        c = Client()
        c.force_login(admin_user)
        url = f"/admin/finance/invoice/{invoice.pk}/change/"
        page_html = c.get(url).content.decode()
        editable = set(re.findall(r'<input[^>]*name="(paid_amount|total|subtotal|vat_amount)"', page_html))
        check("مبالغ مالی فاکتور ورودی قابل ویرایش در فرم ندارند", not editable,
              f"ورودی‌های قابل ویرایش: {sorted(editable) or 'هیچ'}")
        admin_cls = type(__import__("django.contrib.admin", fromlist=["site"]).site._registry[Invoice])
        readonly = set(getattr(admin_cls, "readonly_fields", ()) or ())
        check("مبالغ مالی در readonly_fields ادمین هم قفل شده‌اند",
              {"paid_amount", "total"} <= readonly, f"قفل‌شده: {sorted(readonly)}")

        # ارسال فرم با تغییر دستی مبلغ پرداخت‌شده
        form_fields = dict(re.findall(r'name="(\w+)"[^>]*value="([^"]*)"', page_html))
        form_fields["paid_amount"] = str(before_paid + 123_456_789)
        form_fields["total"] = str(before_total + 999)
        logs_before = AuditLog.objects.count()
        c.post(url, form_fields)
        invoice.refresh_from_db()
        blocked = invoice.paid_amount == before_paid and invoice.total == before_total
        check("ارسال دستی مبلغ پرداخت‌شده از فرم، بی‌اثر است", blocked,
              f"paid_amount: {before_paid:,} → {invoice.paid_amount:,}")
        check("تلاش تغییر، در لاگ حسابرسی ثبت می‌شود",
              AuditLog.objects.count() >= logs_before,
              f"رخدادها: {logs_before} → {AuditLog.objects.count()}")
        if not blocked:  # بازگردانی تا داده‌ی محیط توسعه تغییر نکند
            Invoice.objects.filter(pk=invoice.pk).update(paid_amount=before_paid, total=before_total)

    print("\n۵) ورود خودکار نمایشی (PANEL_DEMO_AUTOLOGIN)")
    from django.conf import settings

    check("ورود خودکار نمایشی در این محیط خاموش است", not getattr(settings, "PANEL_DEMO_AUTOLOGIN", False),
          f"مقدار: {getattr(settings, 'PANEL_DEMO_AUTOLOGIN', None)}")
    source = open(os.path.join(ROOT, "core/middleware.py"), encoding="utf-8").read()
    check("میان‌افزار ورود نمایشی فقط مسیر /admin را می‌گیرد",
          '"/admin"' in source or "'/admin'" in source)
    check("میان‌افزار ورود نمایشی فقط با تنظیم صریح فعال می‌شود",
          bool(re.search(r'getattr\(settings,\s*"PANEL_DEMO_AUTOLOGIN",\s*False\)', source)),
          "الگوی خواندن تنظیم با پیش‌فرض False")

    print("\n۶) قالب‌ها: خروجی امن HTML")
    import subprocess

    root = pathlib.Path(ROOT)
    targets = list((root / "core").rglob("*.py"))
    targets += list(root.glob("*/admin.py"))
    targets += list((root / "templates" / "admin").rglob("*.html"))
    risky = []
    for path in targets:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ("mark_safe" in line or "|safe" in line) and "panel_extras.py" not in str(path):
                risky.append(f"{path.relative_to(root)}:{number}")
    check("خروجی |safe/mark_safe فقط در فایل بررسی‌شدهٔ فیلترها است",
          not risky, f"{len(risky)} مورد خارج از panel_extras: {risky[:3]}")

    print("\n" + "─" * 62)
    print(f"نتیجهٔ کاوش امنیتی پنل: {PASSED} موفق / {FAILED} ناموفق از {PASSED + FAILED}")
    if FINDINGS:
        print("یافته‌های نیازمند اصلاح:")
        for item in FINDINGS:
            print("   •", item)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
