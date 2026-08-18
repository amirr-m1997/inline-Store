import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from apps.notifications.config import parse_env_bool

BASE_DIR = Path(__file__).resolve().parent.parent

for _dotenv_path in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
    if _dotenv_path.is_file():
        load_dotenv(_dotenv_path, override=False)
        break
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-development-key-change-me")
DEBUG = parse_env_bool(os.environ.get("DEBUG"), default=True)
if not DEBUG and SECRET_KEY == "unsafe-development-key-change-me":
    raise ImproperlyConfigured("SECRET_KEY must be set to a secure value when DEBUG is disabled.")
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]
# Mock payments exist only for development. When disabled, checkout refuses to
# create mock gateway payments and the mock-complete endpoint is turned off,
# so orders can never be "verified" without a real gateway.
PAYMENTS_MOCK_ENABLED = parse_env_bool(os.environ.get("PAYMENTS_MOCK_ENABLED"), default=DEBUG)
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "corsheaders", "rest_framework", "rest_framework.authtoken",
    "apps.accounts", "apps.catalog", "apps.inventory", "apps.pricing", "apps.carts", "apps.orders", "apps.dashboard", "apps.company", "apps.website", "apps.content", "apps.search", "apps.rfq", "apps.common", "apps.notifications",
]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", "django.middleware.security.SecurityMiddleware", "config.csrf.CookieAuthOriginCheckMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
# Database selection:
#  - SQLite (default, zero-config) for local development: backend/db.sqlite3.
#  - SQLite in-memory for isolated verification runs: SQLITE_PATH=:memory:.
#  - PostgreSQL whenever the POSTGRES_* variables from docker-compose are present.
if os.environ.get("POSTGRES_HOST") or os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "company_store"),
            "USER": os.environ.get("POSTGRES_USER", "store"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("SQLITE_PATH") or (BASE_DIR / "db.sqlite3")}}
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [
    value.strip()
    for value in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:3005,http://localhost:3006,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3005,http://127.0.0.1:3006"
    ).split(",")
    if value.strip()
]
CORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_SSL_REDIRECT = parse_env_bool(os.environ.get("SECURE_SSL_REDIRECT"), default=False)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 60,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"], "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.CookieTokenAuthentication"], "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination", "PAGE_SIZE": 20, "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema", "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.OrderingFilter"], "DEFAULT_THROTTLE_RATES": {"auth": "10/min", "otp": "5/hour", "discount": "30/min"}}
AUTH_COOKIE_NAME = "mehrasl_auth"
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = "Lax"
OTP_EXPIRY_SECONDS = int(os.environ.get("OTP_EXPIRY_SECONDS", "120"))
OTP_RESEND_SECONDS = int(os.environ.get("OTP_RESEND_SECONDS", "60"))
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3000")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@mehrasl.local")
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = parse_env_bool(os.environ.get("EMAIL_USE_TLS"), default=False)
EMAIL_USE_SSL = parse_env_bool(os.environ.get("EMAIL_USE_SSL"), default=False)
NOTIFICATIONS_REAL_DELIVERY_ENABLED = parse_env_bool(os.environ.get("NOTIFICATIONS_REAL_DELIVERY_ENABLED"), default=False)
NOTIFICATIONS_EMAIL_ENABLED = parse_env_bool(os.environ.get("NOTIFICATIONS_EMAIL_ENABLED"), default=False)
NOTIFICATIONS_SMS_ENABLED = parse_env_bool(os.environ.get("NOTIFICATIONS_SMS_ENABLED"), default=False)
NOTIFICATIONS_MAX_ATTEMPTS = int(os.environ.get("NOTIFICATIONS_MAX_ATTEMPTS", "3"))
SMS_USERNAME = os.environ.get("SMS_USERNAME", "")
SMS_PASSWORD = os.environ.get("SMS_PASSWORD", "")
SMS_PORTAL = os.environ.get("SMS_PORTAL", "")
SMS_BACKEND = os.environ.get("SMS_BACKEND", "")
SALES_NOTIFICATION_EMAIL = os.environ.get("SALES_NOTIFICATION_EMAIL", "")
SALES_NOTIFICATION_SMS = os.environ.get("SALES_NOTIFICATION_SMS", "")
