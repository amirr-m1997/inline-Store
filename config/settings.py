"""
تنظیمات پروژه پنل ادمین صنعتی مهراصل
Django 5.2 + django-unfold + django-import-export
"""
import os
from pathlib import Path

from django.templatetags.static import static

from core.model_docs import help_for_path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me-in-production-########"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# در محیط توسعه/پیش‌نمایش همه‌ی هاست‌ها مجازند تا از طریق پراکسی باز شود؛
# در محیط عملیاتی باید فهرست دامنه‌ها با DJANGO_ALLOWED_HOSTS داده شود (پیش‌فرض: خالی = بستن).
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    "https://*.e2b.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if os.environ.get("DJANGO_CSRF_EXTRA"):
    CSRF_TRUSTED_ORIGINS += os.environ["DJANGO_CSRF_EXTRA"].split(",")

INSTALLED_APPS = [
    # Unfold باید پیش از django.contrib.admin باشد
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "import_export",
    # اپ‌های پروژه
    "core.apps.CoreConfig",
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "inventory.apps.InventoryConfig",
    "pricing.apps.PricingConfig",
    "customers.apps.CustomersConfig",
    "quotes.apps.QuotesConfig",
    "orders.apps.OrdersConfig",
    "finance.apps.FinanceConfig",
    "shop.apps.ShopConfig",  # سایت مشتری (فروشگاه B2B)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ثبت کاربر جاری برای لاگ حسابرسی
    "core.middleware.CurrentUserMiddleware",
    # ورود خودکار در محیط دمو (فقط وقتی PANEL_DEMO_AUTOLOGIN=1)
    "core.middleware.DemoAutoLoginMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "shop.context.shop_context",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.panel_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]

LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/profile/"
LOGOUT_REDIRECT_URL = "/"
SESSION_COOKIE_NAME = "mehraslpanelid"
CSRF_COOKIE_NAME = "mehraslpanelcsrftoken"

# ---------------------------------------------------------------- کسب‌وکار
# واحد پول پروژه: تومان (عدد صحیح). نمایش در رابط کاربری به «میلیون تومان» تبدیل می‌شود.
CURRENCY_UNIT = "تومان"
VAT_RATE = 9  # درصد مالیات بر ارزش افزوده
RFQ_SLA_HOURS = {"urgent": 4, "normal": 24, "project": 72}
DEFAULT_CREDIT_TERMS = "net30"
# ساعت کاری برای محاسبه‌ی SLA (۸ صبح تا ۱۷)
SLA_WORK_HOURS = (8, 17)

# ---------------------------------------------------------------- Unfold
UNFOLD = {
    "SITE_TITLE": "پنل مدیریت مهراصل",
    "SITE_HEADER": "مرکز عملیات فروش B2B",
    "SITE_SUBHEADER": "سایت صنعتی مهراصل — تهویه مطبوع و تبرید صنعتی",
    "SITE_URL": "/",
    "SITE_SYMBOL": "ac_unit",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "ENVIRONMENT": "core.context_processors.environment_callback",
    "DASHBOARD_CALLBACK": "core.dashboard.dashboard_callback",
    # مسیرهای استاتیک باید مطلق باشند؛ وگرنه در صفحه‌های تودرتو (مثل /admin/reports/)
    # مرورگر نشانی نسبی را نسبت به همان صفحه تفسیر می‌کند و CSS بارگذاری نمی‌شود.
    "STYLES": [lambda request: static("css/panel.css")],
    # اسکریپت کوچک پنل: برچسب‌های دسترس‌پذیری + تبدیل تاریخ شمسی/میلادی
    "SCRIPTS": [lambda request: static("js/panel.js")],
    "COLORS": {
        "primary": {
            "50": "#ecfeff",
            "100": "#cffafe",
            "200": "#a5f3fc",
            "300": "#67e8f9",
            "400": "#22d3ee",
            "500": "#06b6d4",
            "600": "#0891b2",
            "700": "#0e7490",
            "800": "#155e75",
            "900": "#164e63",
            "950": "#083344",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "عملیات فروش",
                "separator": True,
                "items": [
                    {"title": "داشبورد عملیاتی", "icon": "dashboard", "link": "/admin/"},
                    {"title": "کارتابل استعلام قیمت", "icon": "forum",
                     "link": "/admin/quotes/quote/"},
                    {"title": "سفارش سریع", "icon": "bolt", "link": "/admin/quick-order/"},
                    {"title": "سفارش‌ها", "icon": "shopping_cart",
                     "link": "/admin/orders/order/"},
                    {"title": "گردش تأیید", "icon": "approval",
                     "link": "/admin/orders/approval/?status=pending"},
                ],
            },
            {
                "title": "کاتالوگ و قیمت",
                "separator": True,
                "items": [
                    {"title": "محصولات", "icon": "inventory_2", "link": "/admin/catalog/product/"},
                    {"title": "دسته‌بندی‌ها", "icon": "category", "link": "/admin/catalog/category/"},
                    {"title": "قالب مشخصات فنی", "icon": "tune",
                     "link": "/admin/catalog/spectemplate/"},
                    {"title": "اسناد و مدارک", "icon": "description",
                     "link": "/admin/catalog/productdocument/"},
                    {"title": "سبدهای قیمت", "icon": "sell", "link": "/admin/pricing/pricelist/"},
                    {"title": "قیمت پلکانی حجمی", "icon": "stacks",
                     "link": "/admin/pricing/quantitypricebreak/"},
                    {"title": "ورود/خروج اکسل", "icon": "upload_file",
                     "link": "/admin/catalog/product/import/"},
                ],
            },
            {
                "title": "انبار",
                "separator": True,
                "items": [
                    {"title": "موجودی", "icon": "warehouse", "link": "/admin/inventory/stockitem/"},
                    {"title": "رسید و حواله", "icon": "swap_horiz",
                     "link": "/admin/inventory/stockmove/"},
                    {"title": "درخواست خرید", "icon": "shopping_bag",
                     "link": "/admin/inventory/purchaserequest/"},
                ],
            },
            {
                "title": "مشتریان و مالی",
                "separator": True,
                "items": [
                    {"title": "حساب‌های سازمانی", "icon": "corporate_fare",
                     "link": "/admin/customers/company/"},
                    {"title": "کاربران مشتری", "icon": "group",
                     "link": "/admin/customers/companyuser/"},
                    {"title": "فاکتورها", "icon": "receipt_long", "link": "/admin/finance/invoice/"},
                    {"title": "چک‌ها و سررسید", "icon": "event_available",
                     "link": "/admin/finance/cheque/"},
                    {"title": "پرداخت‌ها", "icon": "payments", "link": "/admin/finance/payment/"},
                ],
            },
            {
                "title": "مدیریت",
                "separator": True,
                "items": [
                    {"title": "گزارش‌ها و خروجی اکسل", "icon": "bar_chart",
                     "link": "/admin/reports/"},
                    {"title": "سیاههٔ حسابرسی", "icon": "policy", "link": "/admin/core/auditlog/"},
                    {"title": "اعلان‌ها", "icon": "notifications",
                     "link": "/admin/core/notification/"},
                    {"title": "کاربران و نقش‌ها", "icon": "manage_accounts",
                     "link": "/admin/auth/user/"},
                    {"title": "گروه‌ها و دسترسی‌ها", "icon": "key",
                     "link": "/admin/auth/group/"},
                ],
            },
        ],
    },
}

# ------------------------------------------------- ورود خودکار محیط دمو
PANEL_DEMO_AUTOLOGIN = os.environ.get("PANEL_DEMO_AUTOLOGIN", "0") == "1"
PANEL_DEMO_USER = os.environ.get("PANEL_DEMO_USER", "admin")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "core": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


# راهنمای شناور (tooltip) روی آیتم‌های سایدبار: متن توضیح هر مدل/صفحه از core.model_docs
# خوانده می‌شود تا کاربر بدون بازکردن صفحه بداند هر بخش چه کاری انجام می‌دهد.
for _group in UNFOLD["SIDEBAR"]["navigation"]:
    for _item in _group["items"]:
        _path = (_item.get("link") or "").split("?")[0]
        _text = help_for_path(_path)
        if _text:
            _item.setdefault("link_attrs", {})["title"] = _text

# ---------------------------------------------------------------- سایت مشتری (فروشگاه)
# درگاه پرداخت شبیه‌سازی‌شده برای دمو؛ در production باید با درگاه واقعی (زرین‌پال/سامان/…) جایگزین شود.
SHOP_MOCK_GATEWAY = os.environ.get("SHOP_MOCK_GATEWAY", "1") == "1"
SHOP_SITE_NAME = "فروشگاه مهراصل"

# ---------------------------------------------------------------- ایمیل
# پیش‌فرض توسعه: چاپ ایمیل در ترمینال (تا «فراموشی گذرواژه» بدون SMTP هم کار کند).
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "فروشگاه مهراصل <no-reply@mehrasl.ir>")
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # اعتبار لینک بازیابی: یک روز

# ---------------------------------------------------------------- امنیت
# این مقادیر در production با متغیرهای محیطی روشن می‌شوند (DJANGO_SECURE=1).
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14          # ۱۴ روز
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # ۵ مگابایت

# فریم‌بندی: در production هدر X-Frame-Options=DENY می‌فرستیم، اما در محیط توسعه/پیش‌نمایش
# سایت باید داخل iframe نمایش داده شود (پنل آنلاین، پیش‌نمایش محیط توسعه)؛ بنابراین میدل‌ور
# clickjacking در آن حالت غیرفعال است و هیچ هدری فرستاده نمی‌شود.
X_FRAME_OPTIONS = "DENY" if os.environ.get("DJANGO_SECURE", "0") == "1" else "SAMEORIGIN"
if X_FRAME_OPTIONS != "DENY":
    MIDDLEWARE = [m for m in MIDDLEWARE if "clickjacking" not in m]

if os.environ.get("DJANGO_SECURE", "0") == "1":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
