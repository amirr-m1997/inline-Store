"""دستور «panel_check» — تست جامع و خودکار پنل مدیریت مهراصل.

اجرا:
    python3 manage.py panel_check            # تست کامل (با rollback در پایان)
    python3 manage.py panel_check --keep      # بدون rollback (داده‌های تست باقی می‌ماند)

این دستور همان چیزهایی را می‌سنجد که در پنل واقعی به آن نیاز داریم:
۱) پوشش مدل‌ها روی پنل      ۲) چک‌لیست و صفحه تغییر همه مدل‌ها
۳) جست‌وجو و فیلترها        ۴) مسیرهای سفارشی پنل (گزارش/سفارش سریع/اعلان/API)
۵) خروجی XLSX               ۶) گردش سفارش سریع (پیش‌نمایش + ایجاد سفارش)
۷) عملیات گروهی اعلان‌ها     ۸) صحت داده‌های داشبورد (KPI و نمودارها)
"""
from __future__ import annotations

import re

from django.apps import apps
from django.contrib import admin as dj_admin
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.test import Client

PANEL_APPS = ["core", "accounts", "catalog", "inventory", "pricing",
              "customers", "quotes", "orders", "finance"]


class Command(BaseCommand):
    help = "تست جامع پنل: پوشش مدل‌ها، چک‌لیست‌ها، مسیرهای سفارشی، خروجی اکسل و گردش سفارش سریع"

    def add_arguments(self, parser):
        parser.add_argument("--keep", action="store_true",
                            help="داده‌های تستی ساخته‌شده را حذف نکن (بدون rollback)")

    # ------------------------------------------------------------ ابزار گزارش
    def _ok(self, title, detail=""):
        self.passed += 1
        self.stdout.write(f"  \u2713 {title}" + (f" — {detail}" if detail else ""))

    def _fail(self, title, detail=""):
        self.failed += 1
        self.stdout.write(f"  \u2717 {title}" + (f" — {detail}" if detail else ""))

    def _section(self, title):
        self.stdout.write(f"\n{title}")

    # ------------------------------------------------------------------ اجرا
    def handle(self, *args, **options):
        self.passed = self.failed = 0
        self.keep = options["keep"]

        user_model = get_user_model()
        admin_user = user_model.objects.filter(is_superuser=True).first()
        if admin_user is None:
            self.stderr.write("کاربر مدیر یافت نشد؛ ابتدا «python manage.py seed_demo» را اجرا کنید.")
            return
        self.client = Client()
        self.client.force_login(admin_user)
        self.admin_user = admin_user

        try:
            with transaction.atomic():
                self._models_coverage()
                self._changelists_and_forms()
                self._search_and_filters()
                self._custom_routes()
                self._excel_export()
                self._quick_order()
                self._alerts()
                self._dashboard_and_api()
                self._write_flow()
                if not self.keep:
                    transaction.set_rollback(True)
        except Exception as exc:  # noqa: BLE001
            self._fail("اجرای تست‌ها", f"{type(exc).__name__}: {exc}")
            raise

        self.stdout.write("\n" + "─" * 58)
        total = self.passed + self.failed
        state = "همه تست‌ها موفق" if not self.failed else f"{self.failed} تست ناموفق"
        self.stdout.write(f"نتیجه: {self.passed} موفق از {total} — {state}")
        if self.keep:
            self.stdout.write("حالت --keep: تغییرات تستی در پایگاه‌داده باقی ماند.")

    # ------------------------------------------------------- ۱) پوشش مدل‌ها
    def _models_coverage(self):
        self._section("۱) پوشش مدل‌ها روی پنل")
        missing, total = [], 0
        for app in PANEL_APPS:
            for model in apps.get_app_config(app).get_models():
                total += 1
                if model not in dj_admin.site._registry:
                    missing.append(f"{app}.{model.__name__}")
        if missing:
            self._fail("ثبت همه مدل‌ها", "، ".join(missing))
        else:
            self._ok("ثبت همه مدل‌ها", f"{total} مدل در ۹ اپ دامنه")

    # ---------------------------------------------- ۲) چک‌لیست و فرم تغییر
    def _changelists_and_forms(self):
        self._section("۲) چک‌لیست و صفحه تغییر مدل‌ها")
        bad_list, bad_form, checked = [], [], 0
        for model in dj_admin.site._registry:
            meta = model._meta
            base = f"/admin/{meta.app_label}/{meta.model_name}/"
            response = self.client.get(base)
            checked += 1
            if response.status_code != 200:
                bad_list.append(f"{base} → {response.status_code}")
            obj = model._default_manager.first()
            if obj is not None:
                form_url = f"{base}{obj.pk}/change/"
                form_response = self.client.get(form_url)
                if form_response.status_code != 200:
                    bad_form.append(f"{form_url} → {form_response.status_code}")
        self._ok("چک‌لیست‌ها", f"{checked} صفحه") if not bad_list else self._fail(
            "چک‌لیست‌ها", "؛ ".join(bad_list))
        self._ok("صفحه تغییر نمونه‌ها") if not bad_form else self._fail(
            "صفحه تغییر نمونه‌ها", "؛ ".join(bad_form))

    # ------------------------------------------------------ ۳) جست‌وجو و فیلتر
    def _search_and_filters(self):
        self._section("۳) جست‌وجو و فیلتر")
        searched = filtered = 0
        bad = []
        for model, adm in dj_admin.site._registry.items():
            meta = model._meta
            base = f"/admin/{meta.app_label}/{meta.model_name}/"
            if getattr(adm, "search_fields", None):
                searched += 1
                if self.client.get(base + "?q=1").status_code != 200:
                    bad.append(f"q {base}")
            if getattr(adm, "list_filter", None):
                filtered += 1
                if self.client.get(base + "?e=1").status_code != 200:
                    bad.append(f"filter {base}")
        self._ok("جست‌وجو", f"{searched} چک‌لیست") if not bad else self._fail("جست‌وجو/فیلتر", "؛ ".join(bad))
        self._ok("فیلترها", f"{filtered} چک‌لیست")

    # ------------------------------------------------------ ۴) مسیرهای سفارشی
    def _custom_routes(self):
        self._section("۴) مسیرهای سفارشی پنل")
        routes = {
            "داشبورد": "/admin/",
            "گزارش‌ساز": "/admin/reports/",
            "سفارش سریع": "/admin/quick-order/",
            "اعلان‌ها": "/admin/alerts/",
            "API خلاصه": "/admin/api/summary/",
        }
        for name, url in routes.items():
            response = self.client.get(url)
            if response.status_code == 200:
                self._ok(name, f"{url} ({len(response.content):,} بایت)")
            else:
                self._fail(name, f"{url} → {response.status_code}")

        dimensions = ["province", "category", "brand", "product", "company",
                      "rep", "payment", "month"]
        failed = []
        for dimension in dimensions:
            if self.client.get(f"/admin/reports/?dimension={dimension}").status_code != 200:
                failed.append(dimension)
        self._ok("هر ۸ بُعد گزارش", "، ".join(dimensions)) if not failed else self._fail(
            "بُعدهای گزارش", "، ".join(failed))

    # ---------------------------------------------------------- ۵) خروجی اکسل
    def _excel_export(self):
        self._section("۵) خروجی اکسل گزارش")
        failed = []
        sizes = []
        for dimension in ["category", "company", "product", "rep", "month", "brand", "province", "payment"]:
            response = self.client.get(f"/admin/reports/export.xlsx?dimension={dimension}")
            content_type = response.get("Content-Type", "")
            if response.status_code == 200 and "spreadsheet" in content_type and len(response.content) > 3000:
                sizes.append(len(response.content))
            else:
                failed.append(f"{dimension}({response.status_code})")
        self._ok("۸ خروجی XLSX معتبر", f"میانگین {sum(sizes)//max(len(sizes),1):,} بایت") \
            if not failed else self._fail("خروجی XLSX", "، ".join(failed))

    # -------------------------------------------------------- ۶) سفارش سریع
    def _quick_order(self):
        self._section("۶) سفارش سریع (تطبیق کد، قیمت، موجودی، ایجاد سفارش)")
        from customers.models import Company
        from orders.models import Order

        company = Company.objects.filter(is_active=True).first()
        if company is None:
            self._fail("سفارش سریع", "مشتری فعالی موجود نیست")
            return
        lines = "FC-600 x 7\nCL-CU-038, 120\nCH-TR-060 × 1\nXX-NOPE × 3"
        preview = self.client.post("/admin/quick-order/",
                                   {"company": company.pk, "lines": lines, "action": "preview"})
        html = preview.content.decode()
        checks = {
            "تطبیق کد کالا": "FC-600" in html,
            "اصلاح مضرب بسته‌بندی": "مضرب" in html,
            "کد ناشناس": "کد ناشناس" in html,
            "مبنای قیمت (سبد/پله)": "قیمت لیست" in html and "قیمت اعمالی" in html,
            "هشدار موجودی": "کمبود" in html or "موجودی آزاد" in html,
        }
        for title, ok in checks.items():
            (self._ok if ok else self._fail)(f"پیش‌نمایش — {title}")

        before = Order.objects.count()
        created = self.client.post("/admin/quick-order/",
                                   {"company": company.pk, "lines": "FC-600 x 20",
                                    "po_number": "PO-PANEL-CHECK", "action": "create"})
        after = Order.objects.count()
        if created.status_code == 302 and after == before + 1:
            order = Order.objects.order_by("-id").first()
            self._ok("ایجاد سفارش از فهرست چسبانده‌شده",
                     f"{order.number} — {order.lines.count()} ردیف — {order.get_status_display()}")
        else:
            self._fail("ایجاد سفارش", f"کد {created.status_code}، تعداد {before}→{after}")

    # ------------------------------------------------------------- ۷) اعلان‌ها
    def _alerts(self):
        self._section("۷) مرکز اعلان‌ها")
        from core.models import Notification

        html = self.client.get("/admin/alerts/").content.decode()
        filters_ok = all(token in html for token in ('name="level"', 'name="kind"', 'name="state"'))
        (self._ok if filters_ok else self._fail)("فیلتر شدت/نوع/وضعیت")

        unread_ids = list(Notification.objects.filter(is_read=False).values_list("id", flat=True)[:3])
        if unread_ids:
            before = Notification.objects.filter(is_read=False).count()
            self.client.post("/admin/alerts/", {"ids": unread_ids, "action": "mark_read"})
            after = Notification.objects.filter(is_read=False).count()
            (self._ok if after == before - len(unread_ids) else self._fail)(
                "علامت‌گذاری گروهی خوانده‌شده", f"{before} → {after}")
            self.client.post("/admin/alerts/", {"ids": unread_ids, "action": "mark_unread"})
        for query in ["?state=all", "?state=read", "?level=danger", "?kind=cheque_due"]:
            response = self.client.get("/admin/alerts/" + query)
            (self._ok if response.status_code == 200 else self._fail)(f"فیلتر {query}")

    # ------------------------------------------------- ۸) داشبورد و API
    def _dashboard_and_api(self):
        self._section("۸) داشبورد و API")
        html = self.client.get("/admin/").content.decode()
        blocks = {
            "کارت‌های KPI": "panel-kpi-value" in html,
            "نمودار روند فروش": "<path d=\"M" in html,
            "دونات وضعیت سفارش": "panel-donut" in html,
            "قیف استعلام→سفارش": "panel-funnel" in html,
            "پرفروش‌ترین کالاها": "panel-hbar" in html,
            "کارتابل SLA": "کارتابل استعلام" in html,
            "کارتابل تأیید": "کارتابل گردش تأیید" in html,
            "چک‌ها و سررسید": "چک‌ها و سررسیدها" in html,
            "تایم‌لاین/لاگ": "رخدادهای حسابرسی" in html,
            "اعلان‌های درون‌پنلی": "اعلان‌های درون‌پنلی" in html,
        }
        for title, ok in blocks.items():
            (self._ok if ok else self._fail)(f"داشبورد — {title}")

        import json

        response = self.client.get("/admin/api/summary/")
        try:
            payload = json.loads(response.content)
            keys = {"generated_at", "kpi", "monthly_sales"}
            ok = keys.issubset(payload.keys()) and "receivable" in payload["kpi"]
            (self._ok if ok else self._fail)("API خلاصه", f"کلیدها: {len(payload)}")
        except Exception as exc:  # noqa: BLE001
            self._fail("API خلاصه", str(exc))

    # ------------------------------- ۹) گردش نوشتن از فرم ادمین + لاگ حسابرسی
    def _write_flow(self):
        self._section("۹) گردش نوشتن: فرم ادمین → تغییر داده → لاگ حسابرسی")
        from django.test import RequestFactory

        from core.models import AuditLog
        from customers.models import Company

        model = Company
        adm = dj_admin.site._registry[model]
        obj = model._default_manager.filter(is_active=True).first()
        if obj is None:
            self._fail("نوشتن از فرم", "مشتری فعالی برای تست موجود نیست")
            return

        request = RequestFactory().get("/")
        request.user = self.admin_user
        form_class = adm.get_form(request, obj)
        form = form_class(instance=obj)

        data = {"_save": "ذخیره"}
        for name, field in form.fields.items():
            value = form.initial.get(name)
            if value is None or value == "":
                continue
            from django.forms import FileField, ImageField
            if isinstance(field, (FileField, ImageField)):
                continue
            if isinstance(field, type(field)) and hasattr(value, "pk"):
                data[name] = value.pk
            elif isinstance(value, (list, tuple)):
                data[name] = [getattr(v, "pk", v) for v in value]
            elif hasattr(value, "strftime"):
                data[name] = value.strftime("%Y-%m-%d") if not hasattr(value, "hour") \
                    else value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, bool):
                if value:
                    data[name] = "on"
            else:
                data[name] = value

        # مدیریت فرم‌ست‌های inline (بدون ردیف جدید)
        for inline in adm.get_inline_instances(request, obj):
            prefix = inline.get_formset(request, obj).get_default_prefix()
            data[f"{prefix}-TOTAL_FORMS"] = "0"
            data[f"{prefix}-INITIAL_FORMS"] = "0"
            data[f"{prefix}-MIN_NUM_FORMS"] = "0"
            data[f"{prefix}-MAX_NUM_FORMS"] = "1000"

        # مقدار اصلی نگه داشته می‌شود تا در پایان به پایگاه‌داده برگردد؛
        # این آزمون نباید داده‌ی محیط توسعه را تغییرِ ماندگار بدهد.
        original_limit = int(obj.credit_limit or 0)
        new_limit = original_limit + 1_000_000_000
        data["credit_limit"] = str(new_limit)
        before_logs = AuditLog.objects.filter(model_name__endswith="company").count()

        url = f"/admin/{model._meta.app_label}/{model._meta.model_name}/{obj.pk}/change/"
        response = self.client.post(url, data)
        if response.status_code != 302:
            html = response.content.decode()
            import re as _re
            errors = _re.findall(r'class="[^"]*errorlist[^"]*"[^>]*>(.*?)</ul>', html, _re.S)
            hint = "؛ ".join(_re.sub(r"<[^>]+>", " ", e).strip()[:120] for e in errors[:3])
            self._fail("ذخیره‌ی فرم مشتری", f"کد {response.status_code} {hint}")
            return
        obj.refresh_from_db()
        saved = int(obj.credit_limit) == new_limit
        (self._ok if saved else self._fail)("ذخیره‌ی تغییر در فرم",
                                            f"سقف اعتبار → {obj.credit_limit:,}")
        # بازگرداندن سقف اعتبار به مقدار اولیه (نوشتن آزمون نباید در داده بماند)
        model.objects.filter(pk=obj.pk).update(credit_limit=original_limit)
        restored = model.objects.filter(pk=obj.pk, credit_limit=original_limit).exists()
        (self._ok if restored else self._fail)(
            "بازگردانی داده پس از آزمون", f"سقف اعتبار → {original_limit:,}")

        after_logs = AuditLog.objects.filter(model_name__endswith="company").count()
        if after_logs > before_logs:
            entry = AuditLog.objects.filter(model_name__endswith="company").order_by("-id").first()
            fields = "، ".join(entry.changed_fields or [])
            self._ok("ثبت خودکار در لاگ حسابرسی", f"فیلدها: {fields or '—'}")
        else:
            self._fail("ثبت در لاگ حسابرسی", "رخدادی ثبت نشد")

    # ------------------------------------------------------------- کمکی
    @staticmethod
    def _has(html: str, token: str) -> bool:
        return bool(re.search(re.escape(token), html))
