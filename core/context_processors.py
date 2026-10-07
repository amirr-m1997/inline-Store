"""متغیرهای سراسری قالب‌ها."""
from django.conf import settings

from .models import AuditLog, Notification
from .utils import today_jalali


def environment_callback(request):
    """برچسب محیط (استیجینگ/تولید) برای نمایش گوشه‌ی پنل."""
    return ["استیجینگ", "warning"]


def panel_globals(request):
    unread = 0
    critical = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        qs = Notification.objects.filter(is_read=False)
        unread = qs.count()
        critical = qs.filter(level__in=[Notification.Level.DANGER, Notification.Level.WARNING]).count()
    return {
        "PANEL_UNREAD_ALERTS": unread,
        "PANEL_CRITICAL_ALERTS": critical,
        "PANEL_CURRENCY": settings.CURRENCY_UNIT,
        "PANEL_TODAY_JALALI": today_jalali(),
        "PANEL_VAT_RATE": settings.VAT_RATE,
    }
