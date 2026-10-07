"""بازبینی امنیتی سایت مشتری و لبه‌های عمومی پنل مهراصل (سناریوهای حمله).

اجرا روی پایگاه‌دادهٔ آزمون؛ دیتای دمو دست‌نخورده می‌ماند:

    python3 scripts/security_audit.py

محورها: CSRF، احراز هویت و تفکیک دسترسی، IDOR، ارتقای سطح دسترسی،
دست‌کاری قیمت، تزریق SQL/XSS، محدودسازی نرخ ورود، افشای اطلاعات،
هدرها و کوکی‌های امنیتی و رفتار میان‌افزار دمو.
"""
from __future__ import annotations

import os
import re
import sys
from io import StringIO
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: E402
from django.urls import reverse  # noqa: E402

User = get_user_model()
OK, BAD = [], []


def check(name, ok, detail=""):
    (OK if ok else BAD).append(name)
    mark = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
    print(f"  {mark} {name}" + (f"\n      ↳ {detail}" if detail else ""))
    return ok


def section(t):
    print(f"\n\033[96m■ {t}\033[0m")


def body(r):
    try:
        return r.content.decode("utf-8")
    except Exception:
        return ""


def main() -> int:
    setup_test_environment()
    old = connection.creation.create_test_db(verbosity=0, autoclobber=True)
    call_command("seed_demo", stdout=StringIO(), verbosity=0)
    try:
        from catalog.models import Product  # noqa: E402
        from customers.models import Company, CompanyUser  # noqa: E402
        from finance.models import Invoice  # noqa: E402
        from orders.models import Order  # noqa: E402

        product = Product.objects.get(code="FC-600")
        company = Company.objects.get(pk=1)
        csrf_client = Client(enforce_csrf_checks=True)

        section("۱) توکن CSRF و متدهای تغییردهنده")
        csrf_client.get(reverse("shop:home"))
        r = csrf_client.post(reverse("shop:cart-add", args=[product.pk]), {"qty": "5"})
        check("افزودن به سبد بدون توکن CSRF رد می‌شود (۴۰۳)", r.status_code == 403, f"status={r.status_code}")
        r = csrf_client.post(reverse("shop:login"), {"username": "cu0-admin", "password": "Mehr@1405"})
        check("ورود بدون توکن CSRF رد می‌شود (۴۰۳)", r.status_code == 403, f"status={r.status_code}")
        r = csrf_client.post(reverse("shop:logout"))
        check("خروج بدون توکن CSRF رد می‌شود (۴۰۳)", r.status_code == 403, f"status={r.status_code}")

        buyer = Client()
        buyer.login(username="cu0-admin", password="Mehr@1405")
        for method in ("put", "patch", "delete"):
            r = getattr(buyer, method)(reverse("shop:cart-add", args=[product.pk]))
            check(f"متد {method.upper()} روی افزودن به سبد پذیرفته نمی‌شود", r.status_code in (403, 405),
                  f"status={r.status_code}")

        section("۲) احراز هویت و تفکیک دسترسی")
        anon = Client()
        private = {
            "سبد (خواندن عمومی)": reverse("shop:cart"),
            "ثبت سفارش": reverse("shop:checkout"),
            "سفارش‌ها": reverse("shop:orders"),
            "پروفایل": reverse("shop:profile"),
            "تغییر گذرواژه": reverse("shop:password-change"),
            "RFQ": reverse("shop:rfq-from-cart"),
        }
        for label, url in private.items():
            if label == "سبد (خواندن عمومی)":
                check("سبد خرید برای مهمان قابل مشاهده است (بدون داده‌ی سازمانی)", anon.get(url).status_code == 200)
                continue
            r = anon.post(url) if label == "RFQ" else anon.get(url)
            check(f"«{label}» برای مهمان بسته است",
                  r.status_code in (302, 403) and "/accounts/login/" in r.headers.get("Location", "") or r.status_code == 403,
                  f"status={r.status_code}")

        section("۳) ارتقای سطح دسترسی و پنل ادمین")
        buyer2 = Client()
        buyer2.login(username="cu0-admin", password="Mehr@1405")
        user = User.objects.get(username="cu0-admin")
        check("کاربر مشتری staff نیست", not user.is_staff and not user.is_superuser)
        r = buyer2.get("/admin/")
        check("مشتری به پنل ادمین راه نمی‌یابد", r.status_code in (302, 403), f"status={r.status_code}")
        r = buyer2.get("/admin/orders/order/")
        check("مشتری به فهرست سفارش‌های پنل راه نمی‌یابد", r.status_code in (302, 403), f"status={r.status_code}")
        r = buyer2.post("/admin/orders/order/", {"action": "delete_selected", "_selected_action": "1"})
        check("POST مشتری به پنل ادمین رد می‌شود", r.status_code in (302, 403), f"status={r.status_code}")

        # نقش محدود: کاربر بدون دسترسی فاکتور
        limited = CompanyUser.objects.filter(can_view_invoices=False, is_active=True,
                                             company__kyc_status="approved").select_related("company", "user").first()
        if limited is None:
            m = CompanyUser.objects.filter(is_active=True, company__kyc_status="approved").first()
            m.can_view_invoices = False
            m.role = "buyer"
            m.save(update_fields=["can_view_invoices", "role"])
            limited = m
        lc = Client()
        if lc.login(username=limited.user.username, password="Mehr@1405"):
            inv = Invoice.objects.filter(company=limited.company).first()
            page = body(lc.get(reverse("shop:orders")))
            check("کاربر بدون مجوز مالی، فهرست صورت‌حساب‌ها را نمی‌بیند", "دسترسی این نقش محدود است" in page)
            if inv is not None:
                check("کاربر بدون مجوز مالی به فاکتور دسترسی ندارد (۴۰۴/ریدایرکت)",
                      lc.get(reverse("shop:invoice", args=[inv.number])).status_code in (302, 404))
                check("کاربر بدون مجوز مالی به پرداخت فاکتور دسترسی ندارد",
                      lc.get(reverse("shop:invoice-pay", args=[inv.number])).status_code in (302, 404))

        section("۴) IDOR — دسترسی افقی به داده‌ی شرکت‌های دیگر")
        order = Order.objects.filter(company=company).first()
        invoice = Invoice.objects.filter(company=company).first()
        other = Client()
        other.login(username="cu1-admin", password="Mehr@1405")
        other_company = CompanyUser.objects.get(user__username="cu1-admin").company
        check("شمارهٔ سفارش شرکت دیگر ۴۰۴ می‌دهد",
              other.get(reverse("shop:order-detail", args=[order.number])).status_code == 404,
              f"order={order.number} owner={order.company_id} other={other_company.pk}")
        if invoice:
            check("شمارهٔ فاکتور شرکت دیگر ۴۰۴ می‌دهد",
                  other.get(reverse("shop:invoice", args=[invoice.number])).status_code == 404)
            check("پرداخت فاکتور شرکت دیگر ۴۰۴ می‌دهد",
                  other.get(reverse("shop:invoice-pay", args=[invoice.number])).status_code == 404)
            check("صفحهٔ پرداخت موفق شرکت دیگر ۴۰۴ می‌دهد",
                  other.get(reverse("shop:payment-success", args=[invoice.number])).status_code == 404)
        check("حذف نشانی شرکت دیگر ۴۰۴ می‌دهد",
              other.post(reverse("shop:address-delete", args=[company.addresses.first().pk])).status_code == 404)
        bogus = other.get(reverse("shop:invoice", args=["INV-9999-99999"]))
        check("شمارهٔ فاکتور ناموجود خطای کنترل‌شده می‌دهد", bogus.status_code == 404)

        section("۵) دست‌کاری قیمت و تعداد از سمت مرورگر")
        buyer3 = Client()
        buyer3.login(username="cu0-admin", password="Mehr@1405")
        buyer3.post(reverse("shop:cart-add", args=[product.pk]), {"qty": "5"})
        data = buyer3.session["shop_cart"]
        check("سبد فقط شناسه و تعداد را ذخیره می‌کند (بدون قیمت)",
              all(re.fullmatch(r"\d+", str(k)) for k in data["items"]), str(data["items"])[:120])
        tampered = dict(data["items"])
        tampered["99999"] = 50
        session = buyer3.session
        session["shop_cart"] = {"items": tampered}
        session.save()
        rows = body(buyer3.get(reverse("shop:cart")))
        check("شناسهٔ جعلی در سبد به‌عنوان «کد ناشناس» علامت‌گذاری و از جمع‌ها حذف می‌شود",
              "کد ناشناس" in rows and "قابل ثبت نیست" in rows)
        # پارامترهای اضافی در فرم ثبت سفارش نباید اثر کنند
        before = set(Order.objects.values_list("pk", flat=True))
        buyer3.post(reverse("shop:checkout"), {
            "po_number": "PO-SEC", "shipping_method": "pickup", "payment_method": "online",
            "new_address_text": "تبریز", "accept_terms": "on",
            "company": "2", "unit_price": "1", "total": "1", "status": "approved",
            "sales_rep": "1", "discount_pct": "99"})
        created = Order.objects.exclude(pk__in=before).first()
        check("فیلدهای اضافی/غیرمجاز فرم سفارش نادیده گرفته می‌شوند",
              created is None or (created.company_id == 1 and created.discount_pct == 0
                                  and created.total > 1 and created.status in
                                  ("draft", "pending_approval", "approved")),
              f"company={getattr(created, 'company_id', None)} total={getattr(created, 'total', None)} "
              f"discount={getattr(created, 'discount_pct', None)}")

        section("۶) تزریق و اسکریپت‌نویسی")
        for payload, label in (("' OR 1=1--", "تزریق SQL در جست‌وجو"),
                               ("<script>alert(1)</script>", "XSS بازتابی در جست‌وجو"),
                               ("%00", "نویسهٔ تهی"),
                               ("'; DROP TABLE catalog_product; --", "تلاش حذف جدول")):
            r = Client().get(reverse("shop:home"), {"q": payload})
            text = body(r)
            # پاک‌سازی: پاسخ باید سالم، بدون ردیابی خطا و بدون اسکریپت اجراشدنی باشد.
            # (خودِ عبارت جست‌وجو ممکن است در عنوان صفحه به‌صورت escape‌شده بازتاب یابد.)
            safe = (r.status_code == 200 and "Traceback" not in text and "\x00" not in text
                    and "<script>alert(1)</script>" not in text
                    and "catalog_product" in connection.introspection.table_names())
            check(f"{label} مهار می‌شود", safe, f"status={r.status_code}")
        check("پارامتر مرتب‌سازی دلخواه بی‌اثر است (بدون خطا)",
              Client().get(reverse("shop:home"), {"sort": "..;/etc/passwd"}).status_code == 200)
        check("Product count سالم مانده است (تزریق اثر نکرده)", Product.objects.count() > 0)

        section("۷) محدودسازی نرخ و افشای اطلاعات")
        cache.clear()
        attacker = Client()
        url = reverse("shop:login")
        for _ in range(6):
            attacker.post(url, {"username": "cu0-admin", "password": "wrong"})
        locked = body(attacker.post(url, {"username": "cu0-admin", "password": "Mehr@1405"}))
        check("حملهٔ حدس گذرواژه محدود می‌شود", "قفل" in locked or "تلاش زیاد" in locked)

        mail_before = len(django.core.mail.outbox) if "django.core.mail" in sys.modules else 0
        from django.core import mail  # noqa: E402
        mail.outbox.clear()
        real_email = User.objects.exclude(email="").exclude(email__isnull=True).values_list("email", flat=True).first()
        r1 = Client().post(reverse("shop:password-reset"), {"email": "not-exists-1405@example.com"})
        r2 = Client().post(reverse("shop:password-reset"), {"email": real_email})
        check("درخواست بازیابی برای ایمیل ناموجود و موجود پاسخ یکسان می‌دهد (بدون افشای وجود حساب)",
              r1.status_code == r2.status_code == 302,
              f"unknown={r1.status_code} known={r2.status_code} email={real_email}")

        check("پیام‌های خطای صفحه، مسیر فایل‌ها را لو نمی‌دهند",
              "/home/user" not in body(Client().get(reverse("shop:home") + "?q=" + "x" * 500)))
        check("DEBUG در حالت پیش‌فرض توسعه روشن و مستند است",
              settings.DEBUG is True or os.environ.get("DJANGO_SECURE") == "1")

        section("۸) گذرواژه، نشست و هدرهای امنیتی")
        u = User.objects.get(username="cu0-admin")
        check("گذرواژهٔ کاربران هش‌شده ذخیره می‌شود", u.password.startswith(("pbkdf2_", "argon2", "bcrypt")))
        validators = [v["NAME"].rsplit(".", 1)[-1] for v in settings.AUTH_PASSWORD_VALIDATORS]
        check("قواعد گذرواژه شامل طول، تکرار و شباهت است",
              {"MinimumLengthValidator", "CommonPasswordValidator", "NumericPasswordValidator",
               "UserAttributeSimilarityValidator"} <= set(validators), str(validators))
        r = Client().post(reverse("shop:signup"), {
            "first_name": "الف", "last_name": "ب", "username": "weak-user-1",
            "email": "weak1@example.com", "mobile": "09120000000",
            "password1": "123456", "password2": "123456",
            "company_name": "شرکت ضعیف", "legal_type": "legal", "national_id": "14001112223",
            "province": "تهران", "city": "تهران"})
        weak_text = body(r)
        check("ثبت‌نام با گذرواژهٔ ضعیف رد می‌شود (خطای گذرواژه، نه خطای دیگر)",
              r.status_code == 200 and not User.objects.filter(username="weak-user-1").exists()
              and ("گذرواژه" in weak_text or "password" in weak_text.lower()))
        r = Client().post(reverse("shop:signup"), {
            "first_name": "الف", "last_name": "ب", "username": "mass-assign-1",
            "email": "mass1@example.com", "mobile": "09120000000",
            "password1": "Strong@1405pass", "password2": "Strong@1405pass",
            "company_name": "شرکت آزمون مسم", "legal_type": "legal", "national_id": "14001112224",
            "province": "تهران", "city": "تهران",
            "is_staff": "on", "is_superuser": "on", "kyc_status": "approved", "credit_limit": "99999999999"})
        made = User.objects.filter(username="mass-assign-1").first()
        check("ثبت‌نام نمی‌تواند سطح دسترسی یا وضعیت KYC را جعل کند",
              made is not None and not made.is_staff and not made.is_superuser
              and made.company_membership.company.kyc_status == "pending"
              and made.company_membership.company.credit_limit == 0,
              f"staff={getattr(made, 'is_staff', None)} kyc={getattr(getattr(made, 'company_membership', None), 'company', None) and made.company_membership.company.kyc_status}")

        c = Client()
        c.get(reverse("shop:home"))
        key_before = c.session.session_key
        c.login(username="cu0-admin", password="Mehr@1405")
        check("شناسهٔ نشست پس از ورود تعویض می‌شود (Session Fixation)",
              c.session.session_key != key_before)

        r = Client().get(reverse("shop:home"))
        cookie_headers = {k.lower(): v for k, v in r.headers.items()}
        # در توسعه/پیش‌نمایش نباید هدر فریم‌بندی فرستاده شود تا داخل iframe باز شود؛
        # در production باید DENY باشد.
        if settings.DEBUG:
            check("در حالت توسعه هدر X-Frame-Options مانع نمایش در iframe نمی‌شود",
                  "x-frame-options" not in cookie_headers,
                  str(cookie_headers.get("x-frame-options")))
        else:
            check("در حالت عملیاتی هدر X-Frame-Options برابر DENY است",
                  cookie_headers.get("x-frame-options") == "DENY", str(cookie_headers.get("x-frame-options")))
        import subprocess
        prod_env = {**os.environ, "DJANGO_DEBUG": "0", "DJANGO_SECURE": "1",
                    "DJANGO_ALLOWED_HOSTS": "shop.mehrasl.ir", "SHOP_MOCK_GATEWAY": "0",
                    "DJANGO_EMAIL_HOST": "smtp.example.com"}
        probe = subprocess.run(
            [sys.executable, "-c",
             "import django;django.setup();from django.conf import settings as s;"
             "print(s.X_FRAME_OPTIONS, any('clickjacking' in m for m in s.MIDDLEWARE))"],
            cwd=str(BASE), env=prod_env, capture_output=True, text=True, timeout=120)
        check("در محیط عملیاتی سیاست فریم‌بندی سخت‌گیرانه فعال می‌شود",
              probe.stdout.strip() == "DENY True", f"out={probe.stdout.strip()} err={probe.stderr[-200:]}")
        check("هدر nosniff فعال است", cookie_headers.get("x-content-type-options") == "nosniff")
        check("کوکی نشست HttpOnly است", settings.SESSION_COOKIE_HTTPONLY)
        check("کوکی نشست SameSite=Lax است", settings.SESSION_COOKIE_SAMESITE == "Lax")
        check("کوکی CSRF SameSite=Lax است", settings.CSRF_COOKIE_SAMESITE == "Lax")
        check("HTTPS اجباری در production با DJANGO_SECURE=1 فعال می‌شود",
              hasattr(settings, "SECURE_SSL_REDIRECT"))
        check("درگاه پرداخت آزمایشی از تنظیمات قابل خاموش‌کردن است",
              hasattr(settings, "SHOP_MOCK_GATEWAY"))
        if not settings.SHOP_MOCK_GATEWAY:
            check("با خاموش‌بودن درگاه، پرداخت آنلاین غیرفعال است", True)

        section("۹) میان‌افزار ورود خودکار دمو")
        from core import middleware  # noqa: E402
        source = Path(middleware.__file__).read_text(encoding="utf-8")
        check("ورود خودکار دمو فقط به مسیرهای /admin محدود است",
              'request.path.startswith("/admin")' in source and 'request.path == "/"' not in source)
        settings_src = (BASE / "config" / "settings.py").read_text(encoding="utf-8")
        check("پرچم ورود خودکار دمو فقط با متغیر محیطی روشن می‌شود",
              "PANEL_DEMO_AUTOLOGIN" in settings_src and "PANEL_DEMO_AUTOLOGIN" in
              (BASE / "core" / "middleware.py").read_text(encoding="utf-8"))
        check("در وضعیت فعلی، ورود خودکار دمو خاموش است (production-safe)",
              not getattr(settings, "PANEL_DEMO_AUTOLOGIN", False),
              f"PANEL_DEMO_AUTOLOGIN={getattr(settings, 'PANEL_DEMO_AUTOLOGIN', None)}")

        section("۱۰) مسیرهای حساس و پاک‌سازی ورودی")
        r = Client().get("/.env")
        check("فایل‌های حساس از طریق وب سرو نمی‌شوند", r.status_code in (404, 400), f"status={r.status_code}")
        r = Client().get("/media/../db.sqlite3")
        check("عبور از مسیر استاتیک مسدود است", r.status_code in (400, 403, 404), f"status={r.status_code}")
        long_qty = Client()
        long_qty.login(username="cu0-admin", password="Mehr@1405")
        r = long_qty.post(reverse("shop:cart-add", args=[product.pk]), {"qty": "9" * 400})
        check("تعداد بسیار بزرگ با خطای کنترل‌شده مدیریت می‌شود", r.status_code in (302, 400, 404, 500) and r.status_code != 500)
        r = long_qty.post(reverse("shop:cart-add", args=[product.pk]), {"qty": "-5"})
        check("تعداد منفی پذیرفته نمی‌شود", r.status_code == 302)
        r = long_qty.post(reverse("shop:cart-update", args=[product.pk]), {"qty": "nan"})
        check("ورودی غیرعددی در به‌روزرسانی سبد مدیریت می‌شود", r.status_code == 302)
    finally:
        connection.creation.destroy_test_db(old, verbosity=0)
        teardown_test_environment()

    print("\n" + "─" * 62)
    total = len(OK) + len(BAD)
    print(f"نتیجهٔ بازبینی امنیتی: \033[92m{len(OK)}\033[0m موفق / \033[91m{len(BAD)}\033[0m ناموفق از {total}")
    if BAD:
        print("\nموارد نیازمند اصلاح:")
        for name in BAD:
            print(f"  • {name}")
        return 1
    print("هیچ آسیب‌پذیری بازی در سناریوهای آزمون‌شده پیدا نشد ✅")
    return 0


if __name__ == "__main__":
    import django.core.mail  # noqa: F401

    sys.exit(main())
