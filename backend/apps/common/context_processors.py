"""Template context shared by the branded admin console."""

from django.conf import settings
from django.utils import timezone

from .jalali import format_jalali


def admin_console(request):
    """Persian console metadata: Jalali date and the running environment.

    The admin footer shows the Jalali date, and a badge marks non-production
    deployments so staff never mistake development data for live data.
    """
    return {
        "mehrasl_today_jalali": format_jalali(timezone.localdate()),
        "mehrasl_environment_slug": "dev" if settings.DEBUG else "prod",
        "mehrasl_environment_label": "محیط توسعه" if settings.DEBUG else "محیط عملیاتی",
    }
