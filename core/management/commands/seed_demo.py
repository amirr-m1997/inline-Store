"""داده‌ی نمونه واقع‌نما برای پنل مهراصل (تهویه مطبوع و تبرید صنعتی).

اجرا:  python manage.py seed_demo
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from accounts.roles import sync_role_groups
from catalog.models import Brand, Category, Product, ProductDocument, ProductRelation, SpecTemplate
from core.audit import log
from core.models import AuditLog
from customers.models import Company, CompanyAddress, CompanyUser
from finance.models import Cheque, Invoice, Payment
from inventory.models import StockItem, StockMove, Warehouse
from orders.models import ApprovalRule, Order, OrderLine
from orders.services import add_event, create_invoice, evaluate_approvals
from pricing.models import PriceList, PriceListItem, QuantityPriceBreak
from quotes.models import Quote, QuoteLine, QuoteMessage
from quotes.services import send_offer

User = get_user_model()
rnd = random.Random(42)


class Command(BaseCommand):
    help = "ساخت داده‌ی نمونه فارسی برای دموی پنل (محصولات، مشتریان، استعلام‌ها، سفارش‌ها، فاکتور و چک)"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="پاک کردن داده‌های نمونه پیش از ساخت")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()
        self.stdout.write("۱) کاربران و نقش‌ها…")
        users = self._users()
        self.stdout.write("۲) دسته‌بندی، برند و قالب مشخصات فنی…")
        categories, templates, brands = self._catalog_base()
        self.stdout.write("۳) محصولات صنعتی…")
        products = self._products(categories, templates, brands, users)
        self.stdout.write("۴) سبدهای قیمت و قیمت پلکانی…")
        price_lists = self._prices(products)
        self.stdout.write("۵) انبار و موجودی…")
        self._stock(products, users)
        self.stdout.write("۶) مشتریان سازمانی…")
        companies = self._companies(price_lists, users)
        self.stdout.write("۷) قواعد گردش تأیید…")
        self._approval_rules()
        self.stdout.write("۸) استعلام‌ها و مذاکره…")
        quotes = self._quotes(companies, products, users)
        self.stdout.write("۹) سفارش‌ها، تأییدها، ارسال و فاکتور…")
        orders = self._orders(companies, products, quotes, users)
        self.stdout.write("۱۰) چک، پرداخت و اعلان‌ها…")
        self._finance(orders, users)
        self.stdout.write("۱۱) چند تغییر قیمت با ثبت در لاگ حسابرسی…")
        self._price_history(products, users)
        self.stdout.write(self.style.SUCCESS(
            f"داده‌ی نمونه ساخته شد: {Product.objects.count()} محصول، "
            f"{Company.objects.count()} مشتری، {Quote.objects.count()} استعلام، "
            f"{Order.objects.count()} سفارش، {Invoice.objects.count()} فاکتور، "
            f"{AuditLog.objects.count()} رکورد حسابرسی."
        ))
        self.stdout.write("ورود پنل: admin / Mehr@1405   (کاربران دیگر با پسورد مشابه: sales1، finance1، store1)")

    # ---------------------------------------------------------------- reset
    def _reset(self):
        for model in (AuditLog, ProductRelation, ProductDocument, StockMove, StockItem, PurchaseRequestStub(),
                      PriceListItem, QuantityPriceBreak, QuoteMessage, QuoteLine, Quote, OrderLine, Order,
                      ApprovalRule, Payment, Cheque, Invoice, CompanyUser, CompanyAddress, Company,
                      Product, Category, Brand, SpecTemplate, PriceList):
            try:
                model.objects.all().delete()
            except Exception:
                pass
        User.objects.exclude(is_superuser=True).delete()

    # ---------------------------------------------------------------- users
    def _users(self):
        sync_role_groups()
        groups = {g.name: g for g in Group.objects.all()}

        def make(username, first, last, role, group_name, discount=0, order_upto=0, staff=True):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "is_staff": staff,
                          "is_active": True, "email": f"{username}@mehrasl.ir"},
            )
            if created:
                user.set_password("Mehr@1405")
                user.save()
            if group_name and group_name in groups:
                user.groups.add(groups[group_name])
            Profile.objects.update_or_create(
                user=user,
                defaults={"role": role, "phone": f"0912{rnd.randint(1000000, 9999999)}",
                          "job_title": {"sales_manager": "مدیر فروش", "sales": "کارشناس فروش",
                                        "warehouse": "مسئول انبار", "finance": "کارشناس مالی",
                                        "content": "مسئول محتوا", "support": "کارشناس فنی",
                                        "sysadmin": "مدیر سیستم"}[role],
                          "branch": "دفتر مرکزی تبریز",
                          "can_approve_discount_upto": discount,
                          "can_approve_order_upto": order_upto,
                          "two_factor_enabled": role in ("sysadmin", "finance")},
            )
            return user

        admin = User.objects.filter(username="admin").first()
        if not admin:
            admin = User.objects.create_superuser("admin", "admin@mehrasl.ir", "Mehr@1405",
                                                  first_name="سیستم", last_name="مدیر")
        Profile.objects.update_or_create(user=admin, defaults={"role": "sysadmin", "job_title": "مدیر سیستم"})

        sales_manager = make("manager", "رضا", "محمدی", "sales_manager", "مدیر فروش", discount=15,
                             order_upto=10_000_000_000)
        sales1 = make("sales1", "مریم", "رضایی", "sales", "کارشناس فروش", discount=5)
        sales2 = make("sales2", "سعید", "کریمی", "sales", "کارشناس فروش", discount=5)
        sales3 = make("sales3", "هما", "نوری", "sales", "کارشناس فروش", discount=3)
        make("finance1", "فرشته", "امینی", "finance", "مالی", order_upto=50_000_000_000)
        make("store1", "خسرو", "انباردار", "warehouse", "انباردار")
        make("content1", "نگار", "شریفی", "content", "محتوا")
        make("tech1", "مهندس", "نوری", "support", "پشتیبانی فنی")
        return {"admin": admin, "manager": sales_manager, "reps": [sales1, sales2, sales3],
                "finance": User.objects.get(username="finance1"),
                "warehouse": User.objects.get(username="store1")}

    # ---------------------------------------------------------------- catalog
    def _catalog_base(self):
        tree = {
            "چیلر": ["چیلر تراکمی", "چیلر جذبی"],
            "فن‌کویل": ["فن‌کویل سقفی", "فن‌کویل کانالی", "فن‌کویل زمینی"],
            "هواساز و پکیج": ["هواساز", "پکیج یونیت", "داکت اسپلیت"],
            "برج خنک‌کننده": ["برج خنک‌کننده فایبرگلاس"],
            "کویل و رادیاتور": ["کویل مسی", "رادیاتور صنعتی"],
            "لوله و اتصالات": ["لوله مسی", "اتصالات برنجی و مسی", "شیرآلات"],
            "عایق برودتی": ["عایق الاستومری", "عایق کائوچو"],
            "قطعات یدکی": ["کمپرسور", "شیر انبساط", "کنترلر"],
        }
        categories, sub_map = {}, {}
        for order, (parent_name, children) in enumerate(tree.items()):
            parent, _ = Category.objects.get_or_create(
                name=parent_name, defaults={"order": order, "code": f"C{order:02d}",
                                            "is_featured": order < 6})
            categories[parent_name] = parent
            for index, child in enumerate(children):
                obj, _ = Category.objects.get_or_create(
                    name=child, parent=parent, defaults={"order": index, "code": f"C{order:02d}{index}"})
                sub_map[child] = obj

        templates = {}
        templates["چیلر"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی چیلر", category=categories["چیلر"],
            defaults={"fields": [
                {"key": "capacity_tr", "label": "ظرفیت سرمایش", "unit": "تن تبرید", "type": "number"},
                {"key": "capacity_kw", "label": "ظرفیت", "unit": "kW", "type": "number"},
                {"key": "compressor", "label": "کمپرسور", "unit": "", "type": "text"},
                {"key": "refrigerant", "label": "مبرد", "unit": "", "type": "text"},
                {"key": "power", "label": "برق مصرفی", "unit": "", "type": "text"},
                {"key": "flow_rate", "label": "دبی آب", "unit": "m³/h", "type": "number"},
                {"key": "power_supply", "label": "برق ورودی", "unit": "", "type": "text"},
                {"key": "dimensions", "label": "ابعاد", "unit": "mm", "type": "text"},
                {"key": "weight", "label": "وزن", "unit": "kg", "type": "number"},
                {"key": "standard", "label": "استاندارد", "unit": "", "type": "text"},
            ]})[0]
        templates["فن‌کویل"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی فن‌کویل", category=categories["فن‌کویل"],
            defaults={"fields": [
                {"key": "airflow", "label": "هوا دهی", "unit": "CFM", "type": "number"},
                {"key": "cooling_capacity", "label": "ظرفیت سرمایش", "unit": "kW", "type": "number"},
                {"key": "coil_rows", "label": "تعداد ردیف کویل", "unit": "", "type": "number"},
                {"key": "motor", "label": "موتور فن", "unit": "", "type": "text"},
                {"key": "static_pressure", "label": "فشار استاتیک", "unit": "Pa", "type": "number"},
                {"key": "noise", "label": "صدا", "unit": "dB", "type": "number"},
                {"key": "water_connection", "label": "اتصال آب", "unit": "inch", "type": "text"},
            ]})[0]
        templates["هواساز"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی هواساز", category=categories["هواساز و پکیج"],
            defaults={"fields": [
                {"key": "airflow", "label": "هوا دهی", "unit": "CFM", "type": "number"},
                {"key": "external_pressure", "label": "فشار خارجی", "unit": "Pa", "type": "number"},
                {"key": "coil_type", "label": "نوع کویل", "unit": "", "type": "text"},
                {"key": "filter", "label": "فیلتر", "unit": "", "type": "text"},
                {"key": "fan_type", "label": "نوع فن", "unit": "", "type": "text"},
                {"key": "body_material", "label": "جنس بدنه", "unit": "", "type": "text"},
            ]})[0]
        templates["برج"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی برج خنک‌کننده", category=categories["برج خنک‌کننده"],
            defaults={"fields": [
                {"key": "capacity_tr", "label": "ظرفیت", "unit": "تن تبرید", "type": "number"},
                {"key": "water_flow", "label": "دبی آب", "unit": "m³/h", "type": "number"},
                {"key": "body", "label": "بدنه", "unit": "", "type": "text"},
                {"key": "fan_count", "label": "تعداد فن", "unit": "", "type": "number"},
                {"key": "approach", "label": "Approach", "unit": "°C", "type": "number"},
            ]})[0]
        templates["لوله"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی لوله و اتصالات", category=categories["لوله و اتصالات"],
            defaults={"fields": [
                {"key": "size", "label": "سایز", "unit": "inch", "type": "text"},
                {"key": "thickness", "label": "ضخامت", "unit": "mm", "type": "number"},
                {"key": "length", "label": "طول شاخه", "unit": "m", "type": "number"},
                {"key": "alloy", "label": "آلیاژ", "unit": "", "type": "text"},
                {"key": "standard", "label": "استاندارد", "unit": "", "type": "text"},
                {"key": "pressure", "label": "فشار کاری", "unit": "bar", "type": "number"},
            ]})[0]
        templates["عایق"] = SpecTemplate.objects.get_or_create(
            name="قالب فنی عایق برودتی", category=categories["عایق برودتی"],
            defaults={"fields": [
                {"key": "thickness", "label": "ضخامت", "unit": "mm", "type": "number"},
                {"key": "density", "label": "دانسیته", "unit": "kg/m³", "type": "number"},
                {"key": "temp_range", "label": "بازه دما", "unit": "°C", "type": "text"},
                {"key": "length", "label": "طول رول", "unit": "m", "type": "number"},
                {"key": "fire_class", "label": "کلاس آتش", "unit": "", "type": "text"},
            ]})[0]

        brands = {}
        for name, country, is_engine in [
            ("BITZER", "آلمان", True), ("Danfoss", "دانمارک", True), ("Ziehl-Abegg", "آلمان", True),
            ("ebm-papst", "آلمان", True), ("Copeland", "آمریکا", True), ("Carrier", "آمریکا", False),
            ("Wilhelm Schmidt", "آلمان", True), ("Hanbell", "تایوان", True), ("مهراصل", "ایران", False),
            ("کاوه", "ایران", False),
        ]:
            brands[name], _ = Brand.objects.get_or_create(
                name=name, defaults={"country": country, "is_internal_engine_brand": is_engine})
        categories.update(sub_map)  # دسترسی مستقیم به زیردسته‌ها با نام
        return categories, templates, brands

    def _products(self, categories, templates, brands, users):
        definitions = [
            # (code, name, subcategory, price(تومان), uom, specs, brand, lead, availability)
            ("CH-TR-060", "چیلر تراکمی اسکرو ۶۰ تن", "چیلر تراکمی", 1_650_000_000, "device",
             {"capacity_tr": 60, "capacity_kw": 211, "compressor": "اسکرو", "refrigerant": "R-134a",
              "power": "45 kW", "flow_rate": 32, "power_supply": "۳ فاز / ۳۸۰V / ۵۰Hz",
              "dimensions": "2600 × 1200 × 1750", "weight": 1450, "standard": "AHRI 550/590"}, "BITZER", 40, "made_to_order"),
            ("CH-TR-100", "چیلر تراکمی اسکرو ۱۰۰ تن", "چیلر تراکمی", 2_400_000_000, "device",
             {"capacity_tr": 100, "capacity_kw": 352, "compressor": "اسکرو", "refrigerant": "R-134a",
              "power": "72 kW", "flow_rate": 54, "power_supply": "۳ فاز / ۳۸۰V / ۵۰Hz",
              "dimensions": "3200 × 1400 × 1900", "weight": 2180, "standard": "AHRI 550/590"}, "BITZER", 45, "made_to_order"),
            ("CH-TR-150", "چیلر تراکمی اسکرو ۱۵۰ تن", "چیلر تراکمی", 3_450_000_000, "device",
             {"capacity_tr": 150, "capacity_kw": 528, "compressor": "اسکرو دوقلو", "refrigerant": "R-134a",
              "power": "108 kW", "flow_rate": 78, "power_supply": "۳ فاز / ۳۸۰V / ۵۰Hz",
              "dimensions": "3800 × 1500 × 2000", "weight": 2950, "standard": "AHRI 550/590"}, "Hanbell", 60, "made_to_order"),
            ("CH-AB-300", "چیلر جذبی ۳۰۰ تن دو اثره", "چیلر جذبی", 8_900_000_000, "device",
             {"capacity_tr": 300, "capacity_kw": 1055, "compressor": "بدون کمپرسور (جذبی)",
              "refrigerant": "آب/لیتیوم بروماید", "power": "7.5 kW پمپ", "flow_rate": 160,
              "power_supply": "۳ فاز / ۳۸۰V", "dimensions": "4200 × 2100 × 2400",
              "weight": 8200, "standard": "AHRI 560"}, "مهراصل", 90, "needs_quote"),
            ("FC-400", "فن‌کویل سقفی ۴۰۰ CFM", "فن‌کویل سقفی", 17_500_000, "device",
             {"airflow": 400, "cooling_capacity": 5.6, "coil_rows": 3, "motor": "ebm — ۳ سرعته",
              "static_pressure": 30, "noise": 42, "water_connection": '1/2"'}, "ebm-papst", 7, "in_stock"),
            ("FC-600", "فن‌کویل سقفی ۶۰۰ CFM", "فن‌کویل سقفی", 24_500_000, "device",
             {"airflow": 600, "cooling_capacity": 8.4, "coil_rows": 4, "motor": "ebm — ۳ سرعته",
              "static_pressure": 40, "noise": 46, "water_connection": '1/2"'}, "ebm-papst", 7, "in_stock"),
            ("FC-800", "فن‌کویل کانالی ۸۰۰ CFM", "فن‌کویل کانالی", 33_000_000, "device",
             {"airflow": 800, "cooling_capacity": 11.2, "coil_rows": 4, "motor": "Ziehl-Abegg",
              "static_pressure": 80, "noise": 48, "water_connection": '3/4"'}, "Ziehl-Abegg", 10, "in_stock"),
            ("FC-1200", "فن‌کویل زمینی ۱۲۰۰ CFM", "فن‌کویل زمینی", 44_500_000, "device",
             {"airflow": 1200, "cooling_capacity": 16.8, "coil_rows": 4, "motor": "Ziehl-Abegg",
              "static_pressure": 50, "noise": 52, "water_connection": '3/4"'}, "Ziehl-Abegg", 14, "in_stock"),
            ("AHU-5000", "هواساز ۵۰۰۰ CFM", "هواساز", 780_000_000, "device",
             {"airflow": 5000, "external_pressure": 400, "coil_type": "۶ ردیف مسی",
              "filter": "G4 + F7", "fan_type": "سانتریفیوژ", "body_material": "گالوانیزه دوجداره"}, "مهراصل", 30, "made_to_order"),
            ("AHU-10000", "هواساز ۱۰۰۰۰ CFM", "هواساز", 1_320_000_000, "device",
             {"airflow": 10000, "external_pressure": 500, "coil_type": "۸ ردیف مسی",
              "filter": "G4 + F8", "fan_type": "سانتریفیوژ تسمه‌ای",
              "body_material": "گالوانیزه دوجداره عایق‌دار"}, "مهراصل", 45, "made_to_order"),
            ("AHU-20000", "هواساز ۲۰۰۰۰ CFM", "هواساز", 2_150_000_000, "device",
             {"airflow": 20000, "external_pressure": 600, "coil_type": "۸ ردیف مسی",
              "filter": "G4 + F9", "fan_type": "سانتریفیوژ", "body_material": "پانل ساندویچی"}, "مهراصل", 60, "made_to_order"),
            ("PKG-25", "پکیج یونیت ۲۵ تن", "پکیج یونیت", 2_850_000_000, "device",
             {"capacity_tr": 25, "refrigerant": "R-410a", "compressor": "اسکرال Copeland",
              "power_supply": "۳ فاز / ۳۸۰V", "weight": 1950}, "Copeland", 45, "made_to_order"),
            ("PKG-40", "پکیج یونیت ۴۰ تن", "پکیج یونیت", 4_100_000_000, "device",
             {"capacity_tr": 40, "refrigerant": "R-410a", "compressor": "اسکرال تاندوم",
              "power_supply": "۳ فاز / ۳۸۰V", "weight": 2800}, "Copeland", 55, "made_to_order"),
            ("CT-FRP-200", "برج خنک‌کننده فایبرگلاس ۲۰۰ تن", "برج خنک‌کننده فایبرگلاس", 620_000_000, "device",
             {"capacity_tr": 200, "water_flow": 62, "body": "FRP ضد UV", "fan_count": 1, "approach": 4}, "مهراصل", 25, "in_stock"),
            ("CT-FRP-400", "برج خنک‌کننده فایبرگلاس ۴۰۰ تن", "برج خنک‌کننده فایبرگلاس", 1_050_000_000, "device",
             {"capacity_tr": 400, "water_flow": 124, "body": "FRP ضد UV", "fan_count": 2, "approach": 4}, "مهراصل", 35, "ready"),
            ("CL-CU-038", "لوله مسی ۳/۸ اینچ (شاخه ۳ متری)", "لوله مسی", 650_000, "branch",
             {"size": '3/8"', "thickness": 1.0, "length": 3, "alloy": "مس خالص ۹۹.۹٪",
              "standard": "ASTM B280", "pressure": 60}, "مهراصل", 5, "in_stock"),
            ("CL-CU-058", "لوله مسی ۵/۸ اینچ (شاخه ۳ متری)", "لوله مسی", 1_150_000, "branch",
             {"size": '5/8"', "thickness": 1.1, "length": 3, "alloy": "مس خالص ۹۹.۹٪",
              "standard": "ASTM B280", "pressure": 55}, "مهراصل", 5, "in_stock"),
            ("CL-CU-078", "لوله مسی ۷/۸ اینچ (شاخه ۳ متری)", "لوله مسی", 1_980_000, "branch",
             {"size": '7/8"', "thickness": 1.2, "length": 3, "alloy": "مس خالص ۹۹.۹٪",
              "standard": "ASTM B280", "pressure": 50}, "مهراصل", 7, "in_stock"),
            ("FT-BR-012", "زانویی برنجی ۱/۲ اینچ", "اتصالات برنجی و مسی", 185_000, "piece",
             {"size": '1/2"', "alloy": "برنج ۶۰/۴۰", "pressure": 25, "standard": "EN 1254"}, "مهراصل", 4, "in_stock"),
            ("FT-BR-034", "زانویی برنجی ۳/۴ اینچ", "اتصالات برنجی و مسی", 268_000, "piece",
             {"size": '3/4"', "alloy": "برنج ۶۰/۴۰", "pressure": 25, "standard": "EN 1254"}, "مهراصل", 4, "in_stock"),
            ("FT-CU-058", "کوپلر مسی ۵/۸ اینچ", "اتصالات برنجی و مسی", 310_000, "piece",
             {"size": '5/8"', "alloy": "مس", "pressure": 30, "standard": "EN 1254"}, "مهراصل", 6, "in_stock"),
            ("VA-BV-012", "شیر توپی برنجی ۱/۲ اینچ", "شیرآلات", 425_000, "piece",
             {"size": '1/2"', "pressure": 16, "standard": "EN 12165"}, "مهراصل", 8, "in_stock"),
            ("IN-EL-13", "عایق الاستومری ۱۳ میل (رول ۲ متری)", "عایق الاستومری", 450_000, "roll",
             {"thickness": 13, "density": 65, "temp_range": "-40 تا +105", "length": 2,
              "fire_class": "B1"}, "مهراصل", 6, "in_stock"),
            ("IN-EL-19", "عایق الاستومری ۱۹ میل (رول ۲ متری)", "عایق الاستومری", 620_000, "roll",
             {"thickness": 19, "density": 65, "temp_range": "-40 تا +105", "length": 2,
              "fire_class": "B1"}, "مهراصل", 6, "in_stock"),
            ("IN-RB-25", "عایق کائوچو ولکانیزه ۲۵ میل", "عایق کائوچو", 890_000, "roll",
             {"thickness": 25, "density": 90, "temp_range": "-30 تا +90", "length": 2,
              "fire_class": "A2"}, "مهراصل", 10, "in_stock"),
            ("CO-KL-025", "کویل مسی صنعتی ۲۵ کیلووات", "کویل مسی", 385_000_000, "set",
             {"capacity_kw": 25, "coil_rows": 4, "alloy": "مس", "pressure": 20}, "مهراصل", 20, "made_to_order"),
            ("CO-KL-070", "کویل مسی صنعتی ۷۰ کیلووات", "کویل مسی", 950_000_000, "set",
             {"capacity_kw": 70, "coil_rows": 6, "alloy": "مس", "pressure": 20}, "مهراصل", 30, "made_to_order"),
            ("RD-IND-120", "رادیاتور صنعتی ۱۲۰۰ اینچ", "رادیاتور صنعتی", 275_000_000, "set",
             {"capacity_kw": 18, "pressure": 10}, "مهراصل", 18, "in_stock"),
            ("CP-SC-05", "کمپرسور اسکرال ۵ تن", "کمپرسور", 425_000_000, "device",
             {"capacity_tr": 5, "refrigerant": "R-410a", "power_supply": "۳ فاز"}, "Copeland", 30, "ready"),
            ("CP-SC-10", "کمپرسور اسکرال ۱۰ تن", "کمپرسور", 780_000_000, "device",
             {"capacity_tr": 10, "refrigerant": "R-410a", "power": "28 kW"}, "Copeland", 35, "made_to_order"),
            ("CP-SC-20", "کمپرسور اسکرو ۲۰ تن", "کمپرسور", 1_450_000_000, "device",
             {"capacity_tr": 20, "refrigerant": "R-134a", "power": "45 kW"}, "Hanbell", 45, "made_to_order"),
            ("CP-SC-10U", "کمپرسور اسکرال ۱۰ تن (کارکرده)", "کمپرسور", 420_000_000, "device",
             {"capacity_tr": 10, "refrigerant": "R-410a"}, "Copeland", 3, "used"),
            ("EX-TX-12", "شیر انبساط ترموستاتیکی ۱۲ تن", "شیر انبساط", 38_500_000, "piece",
             {"capacity_tr": 12, "refrigerant": "R-410a"}, "Danfoss", 14, "in_stock"),
            ("EX-EE-25", "شیر انبساط الکترونیکی ۲۵ تن", "شیر انبساط", 96_000_000, "piece",
             {"capacity_tr": 25, "refrigerant": "R-134a"}, "Danfoss", 21, "in_stock"),
            ("CN-DX-01", "کنترلر دیجیتال چیلر", "کنترلر", 145_000_000, "device",
             {"protocol": "Modbus RTU / TCP", "screen": "لمسی ۷ اینچ"}, "Danfoss", 21, "in_stock"),
            ("CN-ECO-02", "کنترلر هوشمند هواساز (اقتصادساز)", "کنترلر", 128_000_000, "device",
             {"protocol": "BMS / BACnet", "screen": "گرافیکی"}, "Danfoss", 25, "in_stock"),
        ]

        products = []
        for code, name, sub_name, price, uom, specs, brand_name, lead, availability in definitions:
            category = categories.get(sub_name) or categories["چیلر"]
            template = None
            for key in ("چیلر", "فن‌کویل", "هواساز", "برج", "لوله", "عایق"):
                candidate = templates[key]
                if candidate.category_id == category.id or (
                    category.parent_id and candidate.category_id == category.parent_id
                ):
                    template = candidate
                    break
            if template is None and category.parent_id:
                template = next((t for t in templates.values()
                                 if t.category_id == category.parent_id), None)
            packaging = {"branch": 10, "piece": 50, "roll": 10, "device": 1, "set": 1}.get(uom, 1)
            # قواعد فروش اختصاصی هر خانواده کالا (MOQ و مضرب بسته‌بندی)
            overrides = {
                "FC-400": (5, 5), "FC-600": (5, 5), "FC-800": (5, 5), "FC-1200": (2, 2),
                "AHU-5000": (1, 1), "AHU-10000": (1, 1), "AHU-20000": (1, 1),
                "CT-FRP-200": (1, 1), "CT-FRP-400": (1, 1),
                "CL-CU-038": (50, 50), "CL-CU-058": (50, 50), "CL-CU-078": (20, 20),
                "FT-BR-012": (100, 100), "FT-BR-034": (100, 100), "FT-CU-058": (50, 50),
                "VA-BV-012": (50, 50), "IN-EL-13": (10, 10), "IN-EL-19": (10, 10),
                "IN-RB-25": (10, 10), "EX-TX-12": (1, 1), "CP-SC-05": (1, 1),
            }
            moq, multiple = overrides.get(code, (packaging, packaging))
            product, _ = Product.objects.get_or_create(
                code=code,
                defaults={
                    "name": name, "name_en": code, "model_number": f"MA-{code}",
                    "category": category, "brand": brands.get(brand_name),
                    "spec_template": template, "base_price": price, "uom": uom,
                    "packaging_multiple": multiple,
                    "min_order_qty": moq,
                    "lead_time_days": lead, "availability": availability,
                    "specs": specs, "warranty_months": 18 if uom == "device" else 12,
                    "weight_kg": specs.get("weight"), "dimensions": specs.get("dimensions", ""),
                    "origin_country": "ایران", "unspsc_code": f"4010{rnd.randint(1000, 9999)}",
                    "short_description": f"{name} — تولید مهراصل، مطابق استانداردهای صنعتی.",
                    "is_featured": code in ("CH-TR-100", "FC-600", "AHU-10000", "CT-FRP-200"),
                    "tags": f"{sub_name},{name.split()[0]}",
                },
            )
            products.append(product)

        by_code = {p.code: p for p in products}
        # اسناد فنی نمونه
        for code in ("CH-TR-100", "AHU-10000", "FC-600", "CT-FRP-200", "CL-CU-038"):
            product = by_code[code]
            for kind, title, approved in [
                ("datasheet", "دیتاشیت فنی", "مهندس نوری"),
                ("drawing", "نقشه ابعادی", "مهندس نوری"),
                ("cert", "گواهی تست کارخانه", "واحد کنترل کیفیت"),
            ]:
                ProductDocument.objects.get_or_create(
                    product=product, kind=kind, title=title,
                    defaults={"version": "1", "is_latest": True,
                              "reviewed_at": timezone.localdate() - timedelta(days=rnd.randint(20, 120)),
                              "approved_by": approved},
                )
        # سازگاری و لوازم جانبی
        relations = [
            ("CH-TR-100", "CT-FRP-200", "compatible", "برج خنک‌کننده متناسب با ظرفیت"),
            ("CH-TR-100", "AHU-10000", "compatible", "سیستم فن‌کویل/هواساز روی چیلر ۱۰۰ تن"),
            ("CH-TR-060", "CT-FRP-200", "compatible", "برج ۲۰۰ تن برای چیلر ۶۰ تن"),
            ("CH-TR-100", "CP-SC-20", "accessory", "کمپرسور یدکی"),
            ("CH-TR-100", "CN-DX-01", "accessory", "کنترلر دیجیتال چیلر"),
            ("CH-TR-100", "CH-TR-060", "substitute", "جایگزین کوچک‌تر برای بار کمتر"),
            ("FC-600", "IN-EL-13", "complement", "عایق‌کاری لوله‌های آب سرد"),
            ("FC-600", "FT-BR-012", "complement", "اتصالات اتصال فن‌کویل"),
            ("AHU-10000", "CO-KL-070", "accessory", "کویل یدکی"),
            ("CP-SC-10", "CP-SC-10U", "substitute", "نسخه کارکرده با قیمت پایین‌تر"),
            ("CL-CU-038", "FT-CU-058", "complement", "کوپلر متناسب با سایز لوله"),
        ]
        for source, target, kind, note in relations:
            ProductRelation.objects.get_or_create(
                product=by_code[source], target=by_code[target], kind=kind, defaults={"note": note})
        return products

    # ---------------------------------------------------------------- prices
    def _prices(self, products):
        today = timezone.localdate()
        lists = {}
        lists["list"] = PriceList.objects.get_or_create(
            name="لیست قیمت رسمی", code="PL-LIST",
            defaults={"kind": "list", "valid_from": today - timedelta(days=60),
                      "valid_until": today + timedelta(days=120),
                      "note": "لیست پایه منتشرشده"})[0]
        lists["partner"] = PriceList.objects.get_or_create(
            name="همکاران (نمایندگی‌ها)", code="PL-PARTNER",
            defaults={"kind": "partner", "discount_pct": 5,
                      "valid_from": today - timedelta(days=30),
                      "valid_until": today + timedelta(days=45)})[0]
        lists["contractor"] = PriceList.objects.get_or_create(
            name="پیمانکاران تأسیسات", code="PL-CONTR",
            defaults={"kind": "contractor", "discount_pct": 7,
                      "valid_from": today - timedelta(days=20),
                      "valid_until": today + timedelta(days=80)})[0]
        lists["project_a"] = PriceList.objects.get_or_create(
            name="پروژه برج اداری A — البرز", code="PL-PRJ-A",
            defaults={"kind": "project", "valid_from": today - timedelta(days=10),
                      "valid_until": today + timedelta(days=4),
                      "note": "قیمت قفل‌شده پروژه؛ در آستانه انقضا"})[0]
        lists["export"] = PriceList.objects.get_or_create(
            name="صادراتی — بازار عراق", code="PL-EXP",
            defaults={"kind": "export", "discount_pct": 3,
                      "valid_from": today - timedelta(days=90),
                      "valid_until": today - timedelta(days=5),
                      "note": "منقضی‌شده؛ نیازمند بازنگری"})[0]

        # اقلام قیمت اختصاصی برای سبد پروژه و همکاران
        project_items = [("CH-TR-100", 2_190_000_000), ("CH-TR-060", 1_500_000_000),
                         ("AHU-5000", 720_000_000), ("FC-600", 20_900_000), ("CT-FRP-200", 570_000_000)]
        by_code = {p.code: p for p in products}
        for code, price in project_items:
            PriceListItem.objects.get_or_create(
                price_list=lists["project_a"], product=by_code[code],
                defaults={"price": price, "valid_until": today + timedelta(days=4)})
        for code, price in [("CH-TR-100", 2_280_000_000), ("FC-600", 21_500_000),
                            ("CL-CU-038", 580_000), ("IN-EL-13", 390_000), ("CP-SC-05", 395_000_000)]:
            PriceListItem.objects.get_or_create(
                price_list=lists["partner"], product=by_code[code],
                defaults={"price": price, "valid_until": today + timedelta(days=45)})
        for code, price in [("CL-CU-038", 610_000), ("IN-EL-13", 415_000), ("FT-BR-012", 172_000),
                            ("CL-CU-058", 1_080_000)]:
            PriceListItem.objects.get_or_create(
                price_list=lists["contractor"], product=by_code[code],
                defaults={"price": price, "valid_until": today + timedelta(days=80)})

        # پله‌های حجمی روی سبد رسمی
        tiers = [
            ("CH-TR-100", [(3, 4), (6, 7)]), ("FC-600", [(50, 6), (150, 9)]),
            ("CL-CU-038", [(50, 5), (200, 8), (500, 11)]), ("IN-EL-13", [(50, 8), (150, 12)]),
            ("CT-FRP-200", [(2, 3), (5, 6)]), ("FT-BR-012", [(100, 7), (500, 12)]),
        ]
        for code, breaks in tiers:
            for min_qty, pct in breaks:
                QuantityPriceBreak.objects.get_or_create(
                    price_list=lists["list"], product=by_code[code], min_qty=min_qty,
                    defaults={"discount_pct": pct, "note": "پله حجمی لیست رسمی"})
        return lists

    # ---------------------------------------------------------------- stock
    def _stock(self, products, users):
        warehouses = {}
        for code, name, kind in [("W1", "انبار مرکزی تبریز", "central"),
                                 ("W2", "انبار کارگاه ۱", "workshop"),
                                 ("W3", "انبار کارگاه ۲", "workshop")]:
            warehouses[code], _ = Warehouse.objects.get_or_create(
                code=code, defaults={"name": name, "kind": kind, "keeper": users["warehouse"],
                                     "address": "شهرک صنعتی شهید سلیمی، آذرشهر"})
        stock_plan = {
            "CH-TR-060": (1, 1, 3, 1), "CH-TR-100": (2, 1, 3, 1), "CH-TR-150": (0, 0, 2, 1),
            "FC-400": (60, 12, 25, 10), "FC-600": (18, 12, 25, 5), "FC-800": (26, 8, 20, 5),
            "FC-1200": (9, 4, 10, 2), "AHU-5000": (4, 2, 2, 1), "AHU-10000": (1, 1, 2, 1),
            "CT-FRP-200": (7, 2, 3, 1), "CT-FRP-400": (3, 1, 2, 1), "CL-CU-038": (120, 90, 800, 50),
            "CL-CU-058": (240, 60, 400, 50), "CL-CU-078": (95, 20, 300, 30),
            "FT-BR-012": (2400, 300, 1000, 100), "FT-BR-034": (1600, 200, 800, 100),
            "FT-CU-058": (820, 120, 600, 50), "VA-BV-012": (540, 80, 400, 50),
            "IN-EL-13": (90, 40, 200, 20), "IN-EL-19": (140, 30, 200, 20), "IN-RB-25": (60, 10, 150, 20),
            "CP-SC-05": (6, 2, 5, 2), "CP-SC-10": (2, 1, 4, 1), "CP-SC-10U": (3, 0, 1, 1),
            "EX-TX-12": (48, 6, 30, 10), "EX-EE-25": (19, 4, 25, 5), "CN-DX-01": (22, 3, 20, 5),
            "CN-ECO-02": (15, 2, 20, 5), "RD-IND-120": (11, 3, 10, 2), "PKG-25": (2, 0, 2, 1),
        }
        by_code = {p.code: p for p in products}
        for code, (on_hand, reserved, reorder, min_level) in stock_plan.items():
            product = by_code.get(code)
            if not product:
                continue
            item, created = StockItem.objects.get_or_create(
                product=product, warehouse=warehouses["W1"],
                defaults={"on_hand": on_hand, "reserved": reserved, "incoming": 0,
                          "reorder_point": reorder, "min_level": min_level,
                          "bin_location": f"A-{rnd.randint(1, 20):02d}"},
            )
            StockMove.objects.get_or_create(
                product=product, warehouse=warehouses["W1"], kind="receipt", qty=on_hand or 1,
                defaults={"reference": f"RCP-{rnd.randint(1000, 9999)}", "counterparty": "خط تولید مهراصل",
                          "created_by": users["warehouse"],
                          "occurred_on": timezone.localdate() - timedelta(days=rnd.randint(5, 60)),
                          "note": "ورود از خط تولید"},
            )
        # چند قلم در کارگاه‌ها
        for code, warehouse_code, qty in [("FC-600", "W2", 12), ("CL-CU-038", "W2", 40),
                                          ("IN-EL-13", "W3", 30), ("FT-BR-012", "W3", 600)]:
            product = by_code.get(code)
            if product:
                StockItem.objects.get_or_create(
                    product=product, warehouse=warehouses[warehouse_code],
                    defaults={"on_hand": qty, "reserved": 0, "reorder_point": 0, "min_level": 0})

    # ---------------------------------------------------------------- customers
    def _companies(self, price_lists, users):
        definitions = [
            ("پیمانکاری البرز", "legal", "10103456789", "411387654321", "تهران", "تهران",
             5_000_000_000, "cheque", 60, "project_a", "approved", "پروژه برج اداری A"),
            ("شرکت سردسازان پارس", "legal", "10102345678", "411345678901", "تهران", "کرج",
             3_000_000_000, "net30", 30, "partner", "approved", ""),
            ("بیمارستان امام رضا (ع)", "legal", "10105678901", "411398765432", "خراسان رضوی", "مشهد",
             4_000_000_000, "net60", 60, "contractor", "approved", "توسعه اورژانس"),
            ("مجتمع فولاد آذر", "legal", "10107890123", "411323456789", "آذربایجان شرقی", "تبریز",
             8_000_000_000, "cheque", 90, "contractor", "approved", ""),
            ("پتروشیمی زاگرس", "legal", "10109012345", "411356789012", "خوزستان", "ماهشهر",
             15_000_000_000, "mixed", 90, "list", "approved", "استعلام رسمی چیلر جذبی"),
            ("تأسیسات نوین آریا", "legal", "10101122334", "411367890123", "اصفهان", "اصفهان",
             1_500_000_000, "cheque", 45, "partner", "approved", ""),
            ("شرکت ساختمانی دماوند", "legal", "10102233445", "411378901234", "البرز", "کرج",
             900_000_000, "net30", 30, "list", "approved", ""),
            ("نمایندگی جنوب (خلیج فارس)", "legal", "10103344556", "411389012345", "فارس", "شیراز",
             2_200_000_000, "net30", 30, "partner", "approved", ""),
            ("مهندس علی کاظمی", "person", "", "", "آذربایجان شرقی", "تبریز",
             300_000_000, "cash", 0, "list", "approved", "خرید پروژه شخصی"),
            ("هتل بین‌المللی کاسپین", "legal", "10104455667", "411390123456", "مازندران", "بابلسر",
             2_600_000_000, "cheque", 60, "contractor", "pending", "مجوز ساخت در جریان"),
            ("شرکت کشت و صنعت دشت", "legal", "10105566778", "411401234567", "خوزستان", "دزفول",
             1_000_000_000, "net30", 30, "contractor", "approved", ""),
            ("کارخانه کاشی البرز", "legal", "10106677889", "411412345678", "قم", "قم",
             3_500_000_000, "credit", 45, "list", "approved", ""),
            ("مشتری مسدود — شرکت خاطی", "legal", "10107788990", "411423456789", "تهران", "تهران",
             0, "cash", 0, "list", "rejected", "بدهی معوق — لیست سیاه"),
            ("تعاونی مسکن مهرگان", "legal", "10108899001", "411434567890", "گیلان", "رشت",
             1_200_000_000, "cheque", 30, "contractor", "approved", ""),
        ]
        companies = []
        reps = users["reps"]
        for index, (name, legal, nid, econ, province, city, credit, terms, days, pl, kyc, note) in enumerate(definitions):
            rep = reps[index % len(reps)] if index % 5 != 4 else users["manager"]
            company, _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    "legal_type": legal, "national_id": nid, "economic_code": econ,
                    "registration_number": f"{rnd.randint(10000, 99999)}",
                    "phone": f"041-{rnd.randint(30000000, 39999999)}",
                    "mobile": f"0914{rnd.randint(1000000, 9999999)}",
                    "email": f"info@{index}mehrasl-customer.ir",
                    "province": province, "city": city,
                    "address": f"{city}، خیابان صنعت، پلاک {rnd.randint(10, 400)}",
                    "postal_code": f"{rnd.randint(1000000000, 9999999999)}",
                    "price_list": price_lists[pl], "payment_terms": terms,
                    "credit_limit": credit, "credit_days": days, "sales_rep": rep,
                    "kyc_status": kyc, "is_active": kyc != "rejected",
                    "is_blacklisted": kyc == "rejected", "note": note,
                    "created_by": users["manager"],
                },
            )
            CompanyAddress.objects.get_or_create(
                company=company, title="دفتر مرکزی",
                defaults={"province": province, "city": city,
                          "address": f"{city}، خیابان صنعت، پلاک {rnd.randint(10, 400)}",
                          "postal_code": f"{rnd.randint(1000000000, 9999999999)}",
                          "contact_name": "واحد خرید", "contact_phone": f"021-{rnd.randint(20000000, 29999999)}",
                          "is_default": True,
                          "loading_note": "تخلیه با لیفتراک — نیاز به هماهنگی قبلی" if index % 3 == 0 else ""},
            )
            if index % 4 == 0:
                CompanyAddress.objects.get_or_create(
                    company=company, title="پای کار پروژه",
                    defaults={"province": province, "city": city, "address": "محل پروژه — هماهنگی با سرپرست سایت",
                              "contact_name": "سرپرست سایت", "is_default": False})

            # کاربران خرید سازمانی
            for role, first, last in [("admin", "مدیر", "خرید"), ("buyer", "کارشناس", "خرید"),
                                      ("approver", "مدیر", "مالی")]:
                username = f"cu{index}-{role}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={"first_name": first, "last_name": last, "is_staff": False,
                              "is_active": True},
                )
                if created:
                    user.set_password("Mehr@1405")
                    user.save()
                CompanyUser.objects.get_or_create(
                    company=company, user=user,
                    defaults={"role": role, "job_title": {"admin": "مدیر خرید", "buyer": "کارشناس خرید",
                                                          "approver": "مدیر مالی"}[role],
                              "phone": f"0915{rnd.randint(1000000, 9999999)}",
                              "approval_limit": {"admin": credit, "buyer": credit // 10,
                                                 "approver": credit}[role],
                              "can_view_invoices": role in ("admin", "approver")},
                )
            companies.append(company)
        return companies

    # ---------------------------------------------------------------- rules
    def _approval_rules(self):
        rules = [
            ("سفارش بالای ۳ میلیارد تومان", "order_amount", 3_000_000_000, "sales_manager", 1),
            ("سفارش بالای ۸ میلیارد تومان (مالی)", "order_amount", 8_000_000_000, "finance", 2),
            ("تخفیف بیش از ۸ درصد", "discount_pct", 8, "sales_manager", 1),
            ("عبور از سقف اعتبار", "credit_exceed", 0, "finance", 1),
        ]
        for name, scope, threshold, role, step in rules:
            ApprovalRule.objects.get_or_create(
                name=name, scope=scope, threshold=threshold,
                defaults={"approver_role": role, "step": step, "is_active": True,
                          "note": "قاعده نمونه قابل ویرایش از پنل"},
            )

    # ---------------------------------------------------------------- quotes
    def _quotes(self, companies, products, users):
        today = timezone.now()
        by_code = {p.code: p for p in products}
        statuses = ["new", "tech_review", "pricing", "sent", "negotiation", "sent", "converted",
                    "lost", "new", "sent", "negotiation", "converted", "tech_review", "sent"]
        quotes = []
        for index in range(34):
            company = companies[index % len(companies)]
            # توزیع یکنواخت استعلام‌ها در ۴۵ روز اخیر (برای نمودار «استعلام به‌تفکیک روز»)
            days_ago = index * 45 // 34
            created = today - timedelta(days=days_ago, hours=rnd.randint(0, 20))
            priority = rnd.choice(["normal", "normal", "project", "urgent"])
            if days_ago > 12:
                # استعلام‌های قدیمی در دنیای واقعی تعیین‌تکلیف شده‌اند
                status = rnd.choice(["converted", "converted", "lost", "converted"])
            else:
                status = statuses[index % len(statuses)]
            if status == "converted":
                priority = "normal"
            quote = Quote.objects.create(
                company=company,
                contact=company.users.first(),
                project_name=rnd.choice(["", "پروژه برج اداری", "توسعه سالن تولید", "ساختمان اداری",
                                         "سردخانه صنعتی", "مجتمع تجاری", "اورژانس بیمارستان"]),
                status=status, priority=priority,
                assigned_to=rnd.choice(users["reps"] + [users["manager"]]),
                created_at=created,
                valid_until=(created + timedelta(days=14)).date(),
                payment_terms=company.get_payment_terms_display(),
                delivery_terms=rnd.choice(["تحویل درب کارخانه", "ارسال با باربری", "حمل و نصب"]),
                delivery_days=rnd.choice([7, 15, 30, 45, 60]),
                customer_note="لطفاً قیمت نهایی و شرایط تحویل اعلام شود.",
                internal_note="" if index % 3 else "سقف تخفیف ۵٪ — بیشتر از این نیاز به تأیید مدیر فروش دارد.",
                created_by=rnd.choice(users["reps"]),
                source=rnd.choice(["site", "panel", "rep", "phone", "email"]),
            )
            # SLA و پاسخ
            if status in ("sent", "negotiation", "converted", "lost"):
                quote.first_response_at = created + timedelta(hours=rnd.randint(1, 20))
            if status in ("new", "tech_review", "pricing"):
                # ترکیب واقعی: بخشی نزدیک مهلت، بخشی سپری‌شده
                roll = index % 4
                if roll == 0 and days_ago >= 2:
                    quote.sla_due_at = timezone.now() - timedelta(hours=rnd.randint(1, 30))    # عبور از SLA
                elif roll == 1:
                    quote.sla_due_at = timezone.now() + timedelta(hours=rnd.randint(2, 8))     # نزدیک مهلت
            quote.save()

            for code, qty in rnd.sample(
                [("CH-TR-100", rnd.choice([1, 2, 3])), ("CH-TR-060", rnd.choice([1, 2])),
                 ("FC-600", rnd.choice([10, 30, 60, 120])), ("FC-400", rnd.choice([20, 40])),
                 ("AHU-5000", rnd.choice([1, 2, 3])), ("AHU-10000", rnd.choice([1, 2])),
                 ("CT-FRP-200", rnd.choice([1, 2, 4])), ("CL-CU-038", rnd.choice([100, 300, 600])),
                 ("IN-EL-13", rnd.choice([50, 120, 300])), ("FT-BR-012", rnd.choice([200, 600])),
                 ("EX-TX-12", rnd.choice([2, 6])), ("CP-SC-05", rnd.choice([1, 2]))],
                k=rnd.randint(1, 4),
            ):
                product = by_code[code]
                line = QuoteLine(quote=quote, product=product, qty=qty,
                                 availability_note=f"زمان تأمین {product.lead_time_days} روز" if product.lead_time_days else "موجود")
                line.apply_price(company=company, save=False)
                line.save()

            if status not in ("new",):
                QuoteMessage.objects.create(
                    quote=quote, author=quote.assigned_to, kind="status", is_internal=True,
                    body=f"وضعیت به «{quote.get_status_display()}» تغییر کرد.",
                    created_at=created + timedelta(hours=rnd.randint(1, 8)),
                )
            if quote.internal_note:
                QuoteMessage.objects.create(
                    quote=quote, author=users["manager"], kind="note", is_internal=True,
                    body=quote.internal_note, created_at=created + timedelta(hours=2))
            if status in ("sent", "negotiation", "converted"):
                QuoteMessage.objects.create(
                    quote=quote, author=quote.assigned_to, kind="offer", is_internal=False,
                    body=f"پیش‌فاکتور نسخه {quote.version} با شرایط تحویل {quote.delivery_days} روزه ارسال شد.",
                    created_at=created + timedelta(hours=rnd.randint(3, 24)))
            if status == "negotiation":
                QuoteMessage.objects.create(
                    quote=quote, author=None, author_name="کارشناس خرید مشتری", kind="message",
                    is_internal=False, body="امکان تخفیف بیشتر یا کاهش زمان تحویل وجود دارد؟",
                    created_at=created + timedelta(days=1))
            quotes.append(quote)
        return quotes

    # ---------------------------------------------------------------- orders
    def _orders(self, companies, products, quotes, users):
        from quotes.services import convert_to_order

        by_code = {p.code: p for p in products}
        orders = []
        converted = [q for q in quotes if q.status == "converted"]
        for quote in converted[:6]:
            order = convert_to_order(quote, user=quote.assigned_to,
                                     po_number=f"PO-{rnd.randint(10000, 99999)}",
                                     payment_method="cheque" if quote.company.payment_terms == "cheque" else "credit")
            orders.append(order)

        today = timezone.now()
        statuses = ["draft", "pending_approval", "pending_approval", "approved", "reserved",
                    "ready", "shipped", "shipped", "delivered", "delivered", "closed", "cancelled"]
        for index in range(96):
            company = companies[index % len(companies)]
            if company.is_blacklisted:
                continue
            # ۳۰ روز آخر «هر روز حداقل یک سفارش» تا نمودار روند ۳۰ روزه پیوسته باشد،
            # بقیه به‌صورت پراکنده در ۶ ماه گذشته.
            days_ago = index if index < 30 else rnd.randint(30, 175)
            placed = today - timedelta(days=days_ago, hours=rnd.randint(0, 20))
            status = rnd.choice(statuses) if days_ago < 12 else rnd.choice(
                ["delivered", "closed", "shipped", "delivered"])
            method = rnd.choice(["cash", "cheque", "credit", "net30", "mixed"])
            order = Order.objects.create(
                company=company, po_number=f"PO-{rnd.randint(10000, 99999)}" if company.requires_po else "",
                project_name=rnd.choice(["", "پروژه بیمارستان", "سالن تولید", "ساختمان اداری", "سردخانه"]),
                status="draft", payment_method=method if method in dict(
                    Order._meta.get_field("payment_method").choices) else "cash",
                payment_terms=company.get_payment_terms_display(),
                discount_pct=rnd.choice([0, 0, 0, 2, 3, 5, 7]),
                shipping_method=rnd.choice(["pickup", "freight", "freight", "install", "customer"]),
                shipping_cost=rnd.choice([0, 0, 25_000_000, 60_000_000, 120_000_000]) if method in ("install", "freight") else 0,
                sales_rep=company.sales_rep, created_by=company.sales_rep,
                ordered_at=placed,
                expected_delivery_at=(placed + timedelta(days=rnd.choice([7, 15, 30, 45]))).date(),
                internal_note="" if index % 4 else "مشتری درخواست کرده پیش از ارسال تماس بگیریم.",
            )
            for code, qty in rnd.sample(
                [("FC-600", rnd.choice([10, 30, 60])), ("FC-400", rnd.choice([20, 40])),
                 ("CL-CU-038", rnd.choice([100, 300])), ("IN-EL-13", rnd.choice([50, 120])),
                 ("FT-BR-012", rnd.choice([200, 600])), ("CT-FRP-200", rnd.choice([1, 2])),
                 ("CH-TR-060", 1), ("AHU-5000", rnd.choice([1, 2])), ("EX-TX-12", rnd.choice([2, 6])),
                 ("CP-SC-05", 1), ("FC-800", rnd.choice([5, 10])), ("VA-BV-012", rnd.choice([50, 150]))],
                k=rnd.randint(1, 4),
            ):
                product = by_code[code]
                from pricing.services import resolve_price

                price = resolve_price(product, company=company, qty=qty)
                OrderLine.objects.create(
                    order=order, product=product, qty=qty, unit_price=price.unit_price,
                    list_price=price.list_price,
                    unit_cost=int(product.base_price * rnd.uniform(0.62, 0.78)),
                    discount_pct=price.total_discount_pct, lead_time_days=product.lead_time_days,
                )
            evaluate_approvals(order, actor=company.sales_rep)

            # بازگرداندن وضعیت به مقدار هدف (برای دموی realistic)
            if status not in ("draft", "pending_approval"):
                order.status = status
                if status in ("approved", "reserved", "ready", "shipped", "delivered", "closed"):
                    order.approved_at = placed + timedelta(hours=6)
                if status in ("shipped", "delivered", "closed"):
                    order.shipped_at = placed + timedelta(days=rnd.randint(3, 20))
                    order.waybill_number = f"WB-{rnd.randint(100000, 999999)}"
                    order.carrier_name = rnd.choice(["باربری البرز", "حمل و نقل آذر", "باربری ماهان"])
                    for line in order.lines.all():
                        line.qty_reserved = 0
                        line.qty_shipped = line.qty
                        line.save(update_fields=["qty_reserved", "qty_shipped"])
                if status in ("delivered", "closed"):
                    order.delivered_at = (order.shipped_at or placed) + timedelta(days=rnd.randint(1, 10))
                order.save()
                # گردش تأیید سفارش‌های نهایی‌شده در دنیای واقعی بسته شده است
                order.approvals.exclude(status="approved").update(
                    status="approved", acted_at=order.approved_at or placed,
                    approver=users["manager"],
                    comment="تأیید در جریان عملیات (داده‌ی نمونه)",
                )
                add_event(order, f"وضعیت: {order.get_status_display()}",
                          "ثبت‌شده در جریان پردازش سفارش", actor=order.sales_rep,
                          kind="status")

            # فاکتور و پرداخت برای سفارش‌های جلوتر
            if status in ("shipped", "delivered", "closed") and rnd.random() > 0.15:
                invoice = create_invoice(order, user=users["finance"], kind="official")
                invoice.issued_at = (order.shipped_at or placed).date()
                invoice.due_date = invoice.issued_at + timedelta(days=company.credit_days or 15)
                from finance.services import submit_to_moadian

                submit_to_moadian(invoice, user=users["finance"])
                if invoice.moadian_status == "submitted" and rnd.random() > 0.2:
                    invoice.moadian_status = "accepted"
                if rnd.random() > 0.45:
                    if rnd.choice([True, False]) and company.credit_days:
                        # پرداخت جزئی
                        amount = int(invoice.total * rnd.choice([0.3, 0.5]))
                        Payment.objects.create(
                            company=company, invoice=invoice, order=order, method="transfer",
                            amount=amount, paid_at=invoice.issued_at + timedelta(days=rnd.randint(3, 25)),
                            reference=f"TR-{rnd.randint(1000000, 9999999)}", bank="ملت",
                            created_by=users["finance"])
                        invoice.paid_amount = amount
                        invoice.status = "partially_paid"
                    else:
                        Payment.objects.create(
                            company=company, invoice=invoice, order=order, method="transfer",
                            amount=invoice.total, paid_at=invoice.issued_at + timedelta(days=rnd.randint(3, 30)),
                            reference=f"TR-{rnd.randint(1000000, 9999999)}", bank="صادرات",
                            created_by=users["finance"])
                        invoice.paid_amount = invoice.total
                        invoice.status = "paid"
                        invoice.settled_at = invoice.paid_at if hasattr(invoice, "paid_at") else None
                elif invoice.due_date < timezone.localdate():
                    invoice.status = "overdue"
                invoice.save()
                order.status = "closed" if invoice.status == "paid" else order.status
                order.save(update_fields=["status"])
            orders.append(order)
        return orders

    # ---------------------------------------------------------------- finance
    def _finance(self, orders, users):
        today = timezone.localdate()
        open_invoices = [inv for inv in Invoice.objects.exclude(status="paid").select_related("company")]
        for index, invoice in enumerate(open_invoices[:40]):
            due = today + timedelta(days=rnd.choice([-20, -5, 2, 5, 12, 25, 40, 60]))
            cheque = Cheque.objects.create(
                company=invoice.company, direction="received",
                number=f"{rnd.randint(100000, 999999)}",
                bank=rnd.choice(["ملت", "صادرات", "پاسارگاد", "سامان", "تجارت"]),
                branch=rnd.choice(["مرکزی", "شعبه آذرشهر", "شعبه ولیعصر"]),
                account_holder=invoice.company.name,
                amount=int(min(invoice.balance or invoice.total, 2_500_000_000)),
                issue_date=due - timedelta(days=60), due_date=due,
                status=rnd.choice(["in_hand", "in_hand", "deposited", "cleared", "bounced"]),
                invoice=invoice, order=invoice.order, created_by=users["finance"],
                note="چک بابت تسویه فاکتور",
            )
            if cheque.status == "cleared":
                cheque.cleared_at = due
                cheque.save(update_fields=["cleared_at"])
                Payment.objects.create(
                    company=invoice.company, invoice=invoice, order=invoice.order, method="cheque",
                    amount=cheque.amount, paid_at=due, bank=cheque.bank,
                    reference=f"چک {cheque.number}", created_by=users["finance"])
            elif cheque.status == "bounced":
                cheque.bounce_reason = "کسر موجودی"
                cheque.save(update_fields=["bounce_reason"])
            elif cheque.status == "deposited":
                cheque.deposited_at = due - timedelta(days=2)
                cheque.save(update_fields=["deposited_at"])

    # ---------------------------------------------------------------- audit
    def _price_history(self, products, users):
        by_code = {p.code: p for p in products}
        changes = [
            ("CL-CU-038", 0.065, "نرخ جهانی مس +۸٪", users["manager"]),
            ("CH-TR-100", 0.021, "افزایش هزینه کمپرسور وارداتی", users["manager"]),
            ("FC-600", 0.056, "افزایش نرخ ورق و مس", users["reps"][0]),
            ("IN-EL-13", 0.04, "افزایش قیمت مواد اولیه عایق", users["reps"][1]),
        ]
        for code, pct, reason, actor in changes:
            product = by_code.get(code)
            if not product:
                continue
            old = product.base_price
            if product.code == "CL-CU-038":
                product.base_price = 650_000
            elif product.code == "CH-TR-100":
                product.base_price = int(old * (1 + pct))
            else:
                product.base_price = int(old * (1 + pct)) if old else 0
            product.save(update_fields=["base_price"])
            log(action=AuditLog.Action.PRICE, instance=product, actor=actor,
                before={"base_price": str(old)}, after={"base_price": str(product.base_price)},
                changed_fields=["base_price"], reason=reason)


def PurchaseRequestStub():
    """در پاک‌سازی فقط برای جلوگیری از خطای import."""

    class _Q:
        def all(self):
            return []

        def delete(self):
            return 0

    return _Q()
