from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "هسته و لاگ حسابرسی"

    def ready(self):
        from . import signals  # noqa: F401
        from .audit import track_all

        track_all()
        patch_jalali_datetimes()


def patch_jalali_datetimes() -> None:
    """نمایش تاریخ/ساعت فیلدهای فقط‌خواندنی با تقویم شمسی و ارقام فارسی.

    جنگو در پنل ادمین برای فیلدهای readonly از `display_for_field` استفاده
    می‌کند و تاریخ را میلادی (با نام ماه فارسی و ارقام لاتین) نشان می‌دهد؛
    برای پنل فارسی ناخواسته است. هر دو محل import این تابع پوشش داده می‌شود:
    `admin.utils` (استفاده‌ی عمومی) و `admin.helpers` (فیلدهای readonly).
    """
    import datetime as _dt
    from functools import wraps

    from django.contrib.admin import helpers as admin_helpers
    from django.contrib.admin import utils as admin_utils
    from django.utils.html import format_html

    from .utils import jalali, jalali_dt

    def wrap(func):
        @wraps(func)
        def wrapper(value, field, empty_value_display, *args, **kwargs):
            if isinstance(value, _dt.datetime):
                return format_html('<span class="panel-datetime">{}</span>', jalali_dt(value))
            if isinstance(value, _dt.date):
                return format_html('<span class="panel-datetime">{}</span>', jalali(value))
            return func(value, field, empty_value_display, *args, **kwargs)

        return wrapper

    admin_utils.display_for_field = wrap(admin_utils.display_for_field)
    admin_helpers.display_for_field = wrap(admin_helpers.display_for_field)

    # پوستهٔ Unfold نسخهٔ خودش را دارد و در سه ماژول import می‌شود.
    try:
        from unfold import fields as unfold_fields
        from unfold import sections as unfold_sections
        from unfold import utils as unfold_utils
    except ImportError:  # پنل بدون پوسته هم باید کار کند
        return
    unfold_utils.display_for_field = wrap(unfold_utils.display_for_field)
    unfold_fields.display_for_field = wrap(unfold_fields.display_for_field)
    unfold_sections.display_for_field = wrap(unfold_sections.display_for_field)
