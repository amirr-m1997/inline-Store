from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"
    verbose_name = "سایت مشتری (فروشگاه B2B)"

    def ready(self) -> None:  # noqa: D102
        from . import checks  # noqa: F401  (ثبت بررسی‌های استقرار)
