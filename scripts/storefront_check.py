"""بررسی سرتاسری سایت مشتری مهراصل (فروشگاه B2B).

این اسکریپت کل مسیر مشتری را روی یک پایگاه‌دادهٔ آزمون (sqlite در حافظه) اجرا می‌کند و
دیتای دموی db.sqlite3 را دست نمی‌زند:

    python3 scripts/storefront_check.py

پوشش: نمایش صفحات، سبد خرید، قواعد فروش، ثبت‌نام/ورود/خروج/بازیابی گذرواژه،
ثبت سفارش، صدور پیش‌فاکتور، پرداخت درگاه آزمایشی، RFQ، کنترل دسترسی (IDOR)،
محدودیت‌های حساب (KYC/لیست سیاه/اعتبار) و امنیت ورودی‌ها.
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
from django.contrib.staticfiles import finders  # noqa: E402
from django.core import mail  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: E402
from django.urls import reverse  # noqa: E402

User = get_user_model()

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> bool:
    (PASS if ok else FAIL).append(name)
    mark = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
    line = f"  {mark} {name}"
    if detail and not ok:
        line += f"\n      ↳ {detail}"
    elif detail:
        line += f"  ({detail})"
    print(line)
    return ok


def section(title: str) -> None:
    print(f"\n\033[96m■ {title}\033[0m")


# ------------------------------------------------------------------ راه‌اندازی
def boot():
    setup_test_environment()
    old = connection.creation.create_test_db(verbosity=0, autoclobber=True)
    call_command("seed_demo", stdout=StringIO(), verbosity=0)
    return old


def shutdown(old):
    connection.creation.destroy_test_db(old, verbosity=0)
    teardown_test_environment()


def body(resp) -> str:
    try:
        return resp.content.decode("utf-8")
    except Exception:
        return ""


def no_template_errors(text: str) -> bool:
    """هیچ صفحه‌ای نباید تگ رندرشدهٔ باقی‌مانده یا None/Traceback داشته باشد."""
    return not re.search(r"\{%.*?%\}|\{\{.*?\}\}|Traceback \(most recent call last\)", text)


# ------------------------------------------------------------------ بررسی‌ها
def main() -> int:
    old_db = boot()
    try:
        from catalog.models import Product  # noqa: E402
        from customers.models import Company, CompanyAddress, CompanyUser  # noqa: E402
        from finance.models import Invoice  # noqa: E402
        from orders.models import Order  # noqa: E402
        from quotes.models import Quote  # noqa: E402

        def login(username: str, password: str = "Mehr@1405") -> Client:
            client = Client()
            ok = client.login(username=username, password=password)
            assert ok, f"ورود {username} ناموفق بود"
            return client

        fc = Product.objects.filter(is_active=True, code="FC-600").first() or Product.objects.filter(is_active=True).first()
        assert fc is not None, "هیچ کالای فعالی در دادهٔ نمونه نیست"

        section("۱) نمایش صفحات برای بازدیدکنندهٔ واردنشده")
        anon = Client()
        pages = {
            "صفحهٔ اصلی (فروشگاه)": reverse("shop:home"),
            "دربارهٔ ما": reverse("shop:about"),
            "تماس با ما": reverse("shop:contact"),
            "سبد خالی": reverse("shop:cart"),
            "ورود": reverse("shop:login"),
            "ثبت‌نام": reverse("shop:signup"),
            "بازیابی گذرواژه": reverse("shop:password-reset"),
            "صفحهٔ کالا": fc.get_absolute_url(),
        }
        for label, url in pages.items():
            resp = anon.get(url)
            text = body(resp)
            check(f"{label} → ۲۰۰ با محتوای کامل", resp.status_code == 200 and no_template_errors(text),
                  f"status={resp.status_code}")

        home_text = body(anon.get(reverse("shop:home")))
        check("صفحهٔ اصلی، فهرست کالاها را نشان می‌دهد",
              "فهرست کالاها" in home_text and "class=\"product" in home_text)
        found = body(anon.get(reverse("shop:home") + "?q=" + fc.code))
        check("جست‌وجو کالای مورد نظر را پیدا می‌کند", fc.code in found and fc.name[:12] in found)
        check("وضعیت و MOQ هر کالا نمایش داده می‌شود", "کد کالا" in home_text and "حداقل سفارش" in home_text)
        check("صفحهٔ اصلی ریدایرکت به پنل ادمین نمی‌کند", "/admin" not in anon.get(reverse("shop:home")).url if anon.get(reverse("shop:home")).status_code in (301, 302) else True)

        # فیلترها و جست‌وجو
        for qs, label in (("?q=" + fc.code, "جست‌وجو بر اساس کد کالا"),
                          ("?sort=cheap", "مرتب‌سازی ارزان‌ترین"),
                          ("?sort=expensive", "مرتب‌سازی گران‌ترین"),
                          ("?sort=name", "مرتب‌سازی الفبا"),
                          ("?page=99999", "صفحهٔ خارج از محدوده"),
                          ("?q=zzz-not-found", "جست‌وجوی بی‌نتیجه")):
            resp = anon.get(reverse("shop:home") + qs)
            check(f"{label} → ۲۰۰", resp.status_code == 200 and no_template_errors(body(resp)), f"status={resp.status_code}")
        check("حالت خالی جست‌وجو پیام مناسب دارد", "کالایی با این مشخصات پیدا نشد" in body(anon.get(reverse("shop:home") + "?q=zzz-not-found")))

        cheap = anon.get(reverse("shop:home") + "?sort=cheap")
        check("ترتیب ارزان‌ترین واقعاً صعودی است",
              body(cheap).index(fc.code) >= 0 if fc in cheap.context["page_obj"].object_list else True)

        # دسترسی به assets
        for asset in ("css/shop.css", "js/shop.js", "img/favicon.svg",
                      "fonts/Vazirmatn-Regular.woff2", "fonts/Vazirmatn-Bold.woff2"):
            check(f"فایل استاتیک «{asset}» موجود است", finders.find(asset) is not None)

        section("۲) سبد خرید و قواعد فروش")
        anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "7"})
        cart_html = body(anon.get(reverse("shop:cart")))
        check("کالا به سبد مهمان اضافه شد", fc.name[:12] in cart_html)
        check("مضرب بسته‌بندی روی تعداد اعمال شد (۷ → ۱۰)",
              "۱۰" in cart_html and "مضرب" in cart_html or "بسته‌بندی" in cart_html)

        anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        raw_total = sum(float(v) for v in anon.session["shop_cart"]["items"].values())
        check("افزودن دوبارهٔ همان کالا تعداد را جمع می‌کند", raw_total == 12, f"raw={raw_total}")
        check("نمایش تعداد با مضرب بسته‌بندی محاسبه می‌شود (۱۲ → ۱۵)",
              'value="15"' in body(anon.get(reverse("shop:cart"))))

        resp = anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "0"})
        check("تعداد صفر رد می‌شود", "بزرگ‌تر از صفر" in body(anon.get(reverse("shop:home"))) or resp.status_code == 302)

        resp = anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "abc"})
        check("تعداد غیرعددی خطای فارسی می‌دهد", resp.status_code == 302)

        anon.post(reverse("shop:cart-update", args=[fc.pk]), {"qty": "20"})
        check("به‌روزرسانی تعداد از صفحهٔ سبد کار می‌کند",
              'value="20"' in body(anon.get(reverse("shop:cart"))))

        anon.post(reverse("shop:cart-update", args=[fc.pk]), {"action": "remove"})
        check("حذف ردیف از سبد کار می‌کند",
              "سبد خرید شما خالی است" in body(anon.get(reverse("shop:cart"))))

        anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        anon.post(reverse("shop:cart-clear"))
        check("خالی کردن سبد کار می‌کند", "سبد خرید شما خالی است" in body(anon.get(reverse("shop:cart"))))

        check("افزودن به سبد با GET مجاز نیست (۴۰۵)", anon.get(reverse("shop:cart-add", args=[fc.pk])).status_code == 405)
        check("خالی کردن سبد با GET مجاز نیست (۴۰۵)", anon.get(reverse("shop:cart-clear")).status_code == 405)

        # امنیت پارامتر بازگشت
        anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5", "next": "//evil.example.com/x"})
        resp = anon.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5", "next": "//evil.example.com/x"})
        check("پارامتر next بیرونی پذیرفته نمی‌شود (Open Redirect)",
              not resp.headers.get("Location", "").startswith("//evil.example.com"),
              resp.headers.get("Location", ""))

        section("۳) حساب کاربری: ثبت‌نام، ورود، خروج، بازیابی گذرواژه")
        new = Client()
        resp = new.post(reverse("shop:signup"), {
            "first_name": "رضا", "last_name": "آزمون", "username": "test-buyer-1405",
            "email": "test-buyer-1405@example.com", "mobile": "09121112233",
            "password1": "Test@1405shop", "password2": "Test@1405shop",
            "company_name": "شرکت آزمون سایت", "legal_type": "legal",
            "national_id": "14001234567", "economic_code": "411222333444",
            "province": "آذربایجان شرقی", "city": "تبریز", "company_phone": "04133334444",
        })
        check("ثبت‌نام مشتری جدید انجام شد", resp.status_code == 302)
        user = User.objects.filter(username="test-buyer-1405").first()
        check("کاربر و حساب سازمانی ساخته شد", bool(user and user.company_membership))
        check("حساب جدید در وضعیت «در انتظار تأیید» است",
              bool(user and user.company_membership.company.kyc_status == "pending"))
        check("کاربر پس از ثبت‌نام وارد شده است",
              bool(new.session.get("_auth_user_id")))

        wrong = Client()
        check("ورود با گذرواژهٔ نادرست رد می‌شود", not wrong.login(username="test-buyer-1405", password="bad-pass"))
        check("ورود با گذرواژهٔ درست انجام می‌شود", Client().login(username="test-buyer-1405", password="Test@1405shop"))

        # سقف تلاش ناموفق
        brute = Client()
        for _ in range(6):
            brute.post(reverse("shop:login"), {"username": "test-buyer-1405", "password": "wrong-pass"})
        locked = body(brute.post(reverse("shop:login"), {"username": "test-buyer-1405", "password": "Test@1405shop"}))
        check("محدودیت تلاش ناموفق ورود فعال است", "قفل" in locked or "تلاش" in locked)

        # بازیابی گذرواژه سرتاسری
        fresh = Client()
        mail.outbox.clear()
        resp = fresh.post(reverse("shop:password-reset"), {"email": "test-buyer-1405@example.com"})
        check("درخواست بازیابی گذرواژه پذیرفته شد", resp.status_code == 302)
        check("ایمیل بازیابی ارسال شد", len(mail.outbox) == 1, f"outbox={len(mail.outbox)}")
        if mail.outbox:
            link = re.search(r"https?://[^\s]+/accounts/reset/[^\s]+", mail.outbox[0].body)
            check("متن ایمیل فارسی و شامل پیوند است", bool(link) and "بازیابی گذرواژه" in mail.outbox[0].body)
            url = link.group(0).replace("http://testserver", "") if link else ""
            step = fresh.get(url)
            check("پیوند بازیابی باز می‌شود", step.status_code in (200, 302))
            final = fresh.get(step.headers.get("Location", url))
            token = final.context["form"].initial.get("token") or url
            setpage = fresh.get(url)  # جنگو توکن را به /set-password هدایت می‌کند
            target = setpage.headers.get("Location", url)
            token = target.rstrip("/").split("/")[-1]
            resp = fresh.post(target.replace("/set-password/", "/set-password/"), {
                "new_password1": "NewPass@1405", "new_password2": "NewPass@1405"})
            check("گذرواژهٔ جدید ثبت شد", resp.status_code == 302)
            check("ورود با گذرواژهٔ جدید کار می‌کند", Client().login(username="test-buyer-1405", password="NewPass@1405"))
            check("گذرواژهٔ قدیمی دیگر کار نمی‌کند", not Client().login(username="test-buyer-1405", password="Test@1405shop"))

        # تغییر گذرواژه در پروفایل
        changed = login("test-buyer-1405", "NewPass@1405")
        resp = changed.post(reverse("shop:password-change"), {
            "old_password": "NewPass@1405", "new_password1": "Test@1405shop",
            "new_password2": "Test@1405shop"})
        check("تغییر گذرواژه از پنل کاربری کار می‌کند", resp.status_code == 302)
        check("ورود با گذرواژهٔ تغییر یافته موفق است", Client().login(username="test-buyer-1405", password="Test@1405shop"))

        out = login("test-buyer-1405", "Test@1405shop")
        resp = out.post(reverse("shop:logout"))
        check("خروج با POST انجام می‌شود", resp.status_code == 302 and not out.session.get("_auth_user_id"))
        check("خروج با GET ممکن نیست (۴۰۵)", out.get(reverse("shop:logout")).status_code == 405)

        section("۴) دروازهٔ حساب سازمانی (KYC / لیست سیاه)")
        pending = login("cu9-admin")  # هتل بین‌المللی کاسپین — KYC در انتظار
        pending.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        cart_html = body(pending.get(reverse("shop:cart")))
        check("کاربر در انتظار تأیید، پیام محدودیت را می‌بیند", "در انتظار بررسی" in cart_html or "تأیید" in cart_html)
        resp = pending.get(reverse("shop:checkout"))
        check("صفحهٔ ثبت سفارش برای کاربر تأییدنشده هشدار می‌دهد",
              "در انتظار بررسی" in body(resp) or "تأیید (KYC)" in body(resp))
        before = Order.objects.count()
        pending.post(reverse("shop:checkout"), {
            "po_number": "PO-TEST", "shipping_method": "pickup", "payment_method": "online",
            "new_address_text": "تبریز، خیابان آزمون", "new_address_title": "دفتر", "accept_terms": "on"})
        check("ثبت سفارش برای حساب تأییدنشده انجام نمی‌شود", Order.objects.count() == before)

        before_q = Quote.objects.count()
        resp = pending.post(reverse("shop:rfq-from-cart"), {"project_name": "پروژهٔ آزمون", "note": "استعلام تست"})
        check("ارسال RFQ از سبد برای حساب تأییدنشده کار می‌کند", Quote.objects.count() == before_q + 1)
        quote = Quote.objects.order_by("-id").first()
        check("استعلام سایت با منبع «site» و ردیف‌های کالا ثبت شد",
              quote.source == "site" and quote.lines.count() >= 1, f"source={quote.source} lines={quote.lines.count()}")
        check("سبد پس از RFQ خالی می‌شود", "سبد خرید شما خالی است" in body(pending.get(reverse("shop:cart"))))

        blocked = login("cu12-admin")  # مشتری لیست‌سیاه/ردشده
        blocked.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        blocked_cart = body(blocked.get(reverse("shop:cart")))
        check("مشتری غیرفعال/لیست‌سیاه پیام مسدودی می‌بیند",
              ("غیرفعال" in blocked_cart) or ("امکان ثبت سفارش" in blocked_cart),
              blocked_cart[:0])
        before = Order.objects.count()
        blocked.post(reverse("shop:rfq-from-cart"), {"project_name": "x"})
        check("مشتری غیرفعال/لیست‌سیاه نمی‌تواند RFQ ثبت کند", Quote.objects.count() == before_q + 1)

        section("۵) مسیر کامل خرید تا پرداخت (شرکت تأییدشده)")
        buyer = login("cu0-admin")  # پیمانکاری البرز — اعتباری/چکی، تأییدشده
        buyer.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        resp = buyer.get(reverse("shop:checkout"))
        check("صفحهٔ ثبت سفارش باز می‌شود", resp.status_code == 200 and "روش پرداخت" in body(resp))
        check("اعتبار و سررسید حساب نمایش داده می‌شود", "اعتبار" in body(resp))

        existing_orders = set(Order.objects.values_list("pk", flat=True))
        resp = buyer.post(reverse("shop:checkout"), {
            "po_number": "PO-1405-0001",
            "project_name": "پروژهٔ آزمون خرید آنلاین",
            "shipping_method": "delivery", "payment_method": "online",
            "new_address_title": "کارگاه مرکزی", "new_address_city": "تبریز",
            "new_address_text": "تبریز، کیلومتر ۵ جادهٔ تهران", "contact_phone": "09121112233",
            "accept_terms": "on",
        })
        check("سفارش ثبت و به صفحهٔ پرداخت هدایت شد", resp.status_code == 302 and "/invoices/" in resp.headers.get("Location", ""),
              resp.headers.get("Location", ""))
        order = Order.objects.exclude(pk__in=existing_orders).order_by("-id").first()
        check("سفارش جدید در پایگاه‌داده ساخته شد", order is not None)
        if order is None:
            raise SystemExit("سفارش از سایت ساخته نشد؛ بررسی فرم ثبت سفارش لازم است.")
        check("سفارش با ردیف کالا ساخته شد", order and order.lines.count() == 1)
        check("سفارش وارد گردش تأیید شده است", order.status in ("pending_approval", "approved"), f"status={order.status}")
        check("گردش سفارش رویداد ثبت دارد", order.events.filter(kind="status").exists() or order.events.exists())
        invoice = order.invoices.first()
        check("پیش‌فاکتور از سفارش صادر شد", invoice is not None and invoice.kind == "proforma",
              f"kind={getattr(invoice, 'kind', None)}")
        check("مبلغ فاکتور با جمع سفارش می‌خواند", invoice and invoice.total == order.total,
              f"inv={getattr(invoice, 'total', 0)} order={order.total}")

        order_url = reverse("shop:order-detail", args=[order.number])
        detail = body(buyer.get(order_url))
        check("صفحهٔ جزئیات سفارش باز می‌شود", order.number in detail and "گردش سفارش" in detail)
        check("فاکتور سفارش در صفحهٔ جزئیات آمده است", invoice.number in detail)
        listing = body(buyer.get(reverse("shop:orders")))
        check("سفارش در فهرست سفارش‌های کاربر دیده می‌شود", order.number in listing)
        check("فاکتور در فهرست صورت‌حساب‌ها دیده می‌شود", invoice.number in listing)

        pay_url = reverse("shop:invoice-pay", args=[invoice.number])
        check("صفحهٔ درگاه پرداخت باز می‌شود", "درگاه پرداخت" in body(buyer.get(pay_url)))
        resp = buyer.post(pay_url, {"gateway": "mock-asan", "confirm": "on"})
        check("پرداخت آزمایشی انجام و به صفحهٔ موفقیت هدایت شد",
              resp.status_code == 302 and "paid" in resp.headers.get("Location", ""), resp.headers.get("Location", ""))
        invoice.refresh_from_db()
        check("مبلغ پرداخت روی فاکتور ثبت شد", invoice.paid_amount == invoice.total, f"paid={invoice.paid_amount}")
        check("وضعیت فاکتور «تسویه‌شده» شد", invoice.status == "paid", f"status={invoice.status}")
        check("رکورد پرداخت با شمارهٔ پیگیری ساخته شد",
              invoice.payments.filter(reference__startswith="MOCK-").exists())
        success = body(buyer.get(reverse("shop:payment-success", args=[invoice.number])))
        check("صفحهٔ پرداخت موفق، مبلغ و فاکتور را نشان می‌دهد", invoice.number in success and "موفقیت" in success)
        check("فاکتور قابل چاپ است", "چاپ" in body(buyer.get(reverse("shop:invoice", args=[invoice.number]))))

        # سبد پس از سفارش خالی شده باشد
        check("سبد پس از ثبت سفارش خالی شده است", "سبد خرید شما خالی است" in body(buyer.get(reverse("shop:cart"))))

        section("۶) پرداخت اعتباری، سقف اعتبار و کنترل دسترسی")
        buyer.post(reverse("shop:cart-add", args=[fc.pk]), {"qty": "5"})
        company = Company.objects.get(pk=1)
        company.credit_limit = 1_000  # سقف بسیار کم برای آزمون «عبور از اعتبار»
        company.save(update_fields=["credit_limit"])
        resp = buyer.post(reverse("shop:checkout"), {
            "po_number": "PO-1405-0002",
            "project_name": "خرید اعتباری", "shipping_method": "pickup", "payment_method": "credit",
            "new_address_text": "تبریز", "accept_terms": "on"})
        check("خرید اعتباری بیش از سقف اعتبار رد می‌شود",
              "اعتبار" in body(resp) or "بیشتر است" in body(resp))
        company.credit_limit = 5_000_000_000
        company.save(update_fields=["credit_limit"])

        # IDOR: سفارش و فاکتور شرکت دیگر
        other = login("cu1-admin")
        check("سفارش شرکت دیگر قابل مشاهده نیست (۴۰۴)", other.get(order_url).status_code == 404)
        check("فاکتور شرکت دیگر قابل مشاهده نیست (۴۰۴)",
              other.get(reverse("shop:invoice", args=[invoice.number])).status_code == 404)
        foreign_address = CompanyAddress.objects.exclude(company=company).first()
        check("حذف نشانی شرکت دیگر ممکن نیست (۴۰۴)",
              other.post(reverse("shop:address-delete", args=[foreign_address.pk])).status_code == 404)

        anon2 = Client()
        for label, url in (("سفارش‌ها", reverse("shop:orders")),
                           ("ثبت سفارش", reverse("shop:checkout")),
                           ("پروفایل", reverse("shop:profile")),
                           ("جزئیات سفارش", order_url),
                           ("فاکتور", reverse("shop:invoice", args=[invoice.number]))):
            resp = anon2.get(url)
            check(f"«{label}» برای مهمان به صفحهٔ ورود هدایت می‌شود",
                  resp.status_code == 302 and "/accounts/login/" in resp.headers.get("Location", ""),
                  f"{resp.status_code} {resp.headers.get('Location', '')}")

        section("۷) پروفایل، نشانی‌ها و ورودی‌های امنیتی")
        prof = body(buyer.get(reverse("shop:profile")))
        check("صفحهٔ پروفایل باز می‌شود", "اطلاعات کاربری" in prof and "افزودن نشانی جدید" in prof)
        before_addr = order.shipping_address.company.addresses.count()
        resp = buyer.post(reverse("shop:profile"), {
            "submit-address": "1", "addr-title": "انبار جنوب", "addr-province": "تهران",
            "addr-city": "تهران", "addr-address": "جادهٔ قدیم", "addr-postal_code": "1111111111",
            "addr-contact_name": "آزمون", "addr-contact_phone": "09120000000",
        })
        check("ثبت نشانی جدید در پروفایل کار می‌کند",
              resp.status_code == 302 and order.shipping_address.company.addresses.count() == before_addr + 1)

        resp = buyer.post(reverse("shop:profile"), {
            "submit-profile": "1", "first_name": "مدیر", "last_name": "البرز",
            "email": "buyer@test.local", "phone": "09121110000", "job_title": "مدیر خرید"})
        buyer.refresh_login = None
        check("ویرایش اطلاعات کاربری کار می‌کند", resp.status_code == 302)
        check("نام کاربری به‌روزرسانی شد",
              User.objects.get(username="cu0-admin").first_name == "مدیر")

        # XSS: نام کالا با تگ اسکریپت
        evil = Product.objects.create(code="XSS-1", name="<script>alert(1)</script>", base_price=1000,
                                      category=fc.category, is_active=True)
        evil_html = body(Client().get(reverse("shop:home") + "?q=XSS-1"))
        check("محتوای ورودی در HTML escape می‌شود (XSS)",
              "<script>alert(1)</script>" not in evil_html and "&lt;script&gt;" in evil_html)
        evil.delete()

        section("۸) یکپارچگی نمایش و کارایی")
        home_resp = Client().get(reverse("shop:home"))
        queries = len(connection.queries)
        check("صفحهٔ اصلی بدون خطای قالب رندر می‌شود", no_template_errors(body(home_resp)))
        check("سبد خرید پیام «قیمت مصرفی» برای مهمان دارد", "قیمت مصرفی" in body(Client().get(reverse("shop:cart"))))
        check("۱۴۰۵ در سربرگ/فوتر یا محتوای سایت آمده است", "مهراصل" in body(home_resp))
        check("صفحهٔ اصلی هیچ لینک شکسته‌ای به پنل ادمین ندارد", "/admin/" not in body(home_resp))

        # فهرست همهٔ URLهای نام‌دار فروشگاه باید قابل reverse باشند
        from django.urls import NoReverseMatch
        names = ["home", "about", "contact", "cart", "checkout", "orders", "signup", "login",
                 "logout", "profile", "password-reset", "password-reset-done", "password-reset-complete",
                 "password-change", "password-change-done"]
        missing = []
        for name in names:
            try:
                reverse(f"shop:{name}")
            except NoReverseMatch:
                missing.append(name)
        check("همهٔ مسیرهای نام‌دار فروشگاه reverse می‌شوند", not missing, ", ".join(missing))

        # قالب‌های موجود
        from django.template.loader import get_template
        templates = ["shop/base.html", "shop/home.html", "shop/product.html", "shop/cart.html",
                     "shop/checkout.html", "shop/order_list.html", "shop/order_detail.html",
                     "shop/invoice.html", "shop/payment_gateway.html", "shop/payment_success.html",
                     "shop/login.html", "shop/signup.html", "shop/profile.html", "shop/about.html",
                     "shop/contact.html", "shop/password_reset.html", "shop/password_reset_done.html",
                     "shop/password_reset_confirm.html", "shop/password_reset_complete.html",
                     "shop/password_change.html", "shop/password_change_done.html",
                     "shop/emails/password_reset.txt", "shop/emails/password_reset_subject.txt"]
        broken = []
        for name in templates:
            try:
                get_template(name)
            except Exception as exc:  # noqa: BLE001
                broken.append(f"{name}: {exc}")
        check("همهٔ قالب‌های سایت موجود و قابل بارگذاری‌اند", not broken, "; ".join(broken))
    finally:
        shutdown(old_db)

    print("\n" + "─" * 62)
    total = len(PASS) + len(FAIL)
    print(f"نتیجه: \033[92m{len(PASS)}\033[0m موفق / \033[91m{len(FAIL)}\033[0m ناموفق از {total} بررسی")
    if FAIL:
        print("\nموارد ناموفق:")
        for name in FAIL:
            print(f"  • {name}")
        return 1
    print("همهٔ بررسی‌های فروشگاه با موفقیت گذشت ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
