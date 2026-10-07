"""اپ کاربران و نقش‌ها.

علاوه بر تنظیمات خود اپ، نام فارسی و خوانا برای اپ‌های داخلی جنگو (`auth`) هم اینجا
تعیین می‌شود؛ چون نام پیش‌فرض ترجمه‌شده‌ی آن («بررسی اصالت و اجازه‌ها») برای کاربر پنل گنگ است.
"""
from django.apps import AppConfig
from django.apps import apps as django_apps


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "کاربران و نقش‌ها"

    def ready(self) -> None:
        # نام فارسی اپ داخلی جنگو برای مدل‌های کاربر و گروه (در صفحهٔ اپ‌ها و سایدبار دیده می‌شود)
        try:
            django_apps.get_app_config("auth").verbose_name = "کاربران و دسترسی‌ها"
        except LookupError:  # pragma: no cover
            pass
