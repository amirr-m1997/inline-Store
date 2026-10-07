"""بررسی‌های استقرار (python manage.py check --deploy) برای سایت مشتری."""
from __future__ import annotations

from django.conf import settings
from django.core.checks import Warning as CheckWarning
from django.core.checks import register


@register()
def shop_deployment_check(app_configs, **kwargs):
    """پرچم‌های خطرناک در محیط عملیاتی را هشدار می‌دهد."""
    issues = []
    if not settings.DEBUG and getattr(settings, "SHOP_MOCK_GATEWAY", False):
        issues.append(CheckWarning(
            "درگاه پرداخت شبیه‌سازی‌شده (SHOP_MOCK_GATEWAY) در حالت غیر-اشکال‌زدایی روشن است.",
            hint="برای محیط عملیاتی متغیر محیطی SHOP_MOCK_GATEWAY=0 را تنظیم و درگاه واقعی را وصل کنید.",
            id="shop.W001",
        ))
    if not settings.DEBUG and "*" in settings.ALLOWED_HOSTS:
        issues.append(CheckWarning(
            "ALLOWED_HOSTS روی «*» است؛ برای محیط عملیاتی فهرست دامنه‌ها را مشخص کنید.",
            hint="متغیر محیطی DJANGO_ALLOWED_HOSTS=shop.mehrasl.ir,panel.mehrasl.ir",
            id="shop.W002",
        ))
    if not settings.DEBUG and not settings.EMAIL_HOST:
        issues.append(CheckWarning(
            "ایمیل خروجی تنظیم نشده است؛ «فراموشی گذرواژه» و اعلان‌ها ارسال نمی‌شوند.",
            hint="DJANGO_EMAIL_HOST/USER/PASSWORD را تنظیم کنید یا از سرویس ایمیل تراکنشی استفاده کنید.",
            id="shop.W003",
        ))
    return issues
