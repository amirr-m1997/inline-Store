"""میان‌ورها: کاربر جاری برای لاگ حسابرسی + ورود خودکار محیط دمو."""
from __future__ import annotations

import logging

from django.conf import settings

from . import audit

logger = logging.getLogger("core")
_local_user = {"user": None}


def get_current_user(request=None):
    if request is not None:
        user = getattr(request, "user", None)
        if user is not None:
            return user
    return _local_user.get("user")


class CurrentUserMiddleware:
    """کاربر جاری را در دسترس سرویس لاگ حسابرسی قرار می‌دهد."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local_user["user"] = getattr(request, "user", None)
        audit.set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            _local_user["user"] = None
        return response


class DemoAutoLoginMiddleware:
    """در محیط دمو اگر PANEL_DEMO_AUTOLOGIN=1 باشد، کاربر ادمین را وارد می‌کند.

    این کار فقط برای نمایش پنل در محیط پیش‌نمایش است و در production باید خاموش باشد.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "PANEL_DEMO_AUTOLOGIN", False):
            user = getattr(request, "user", None)
            if user is None or not user.is_authenticated:
                # فقط مسیرهای پنل؛ مسیر «/» از این پس سایت مشتری (فروشگاه) است و
                # نباید بازدیدکننده با کاربر ادمین وارد شود.
                if request.path.startswith("/admin"):
                    from django.contrib.auth import get_user_model
                    from django.contrib.auth import login

                    username = getattr(settings, "PANEL_DEMO_USER", "admin")
                    try:
                        demo_user = get_user_model().objects.get(
                            username=username, is_staff=True, is_active=True
                        )
                    except get_user_model().DoesNotExist:
                        demo_user = None
                    if demo_user is not None:
                        login(request, demo_user)
                        request.user = demo_user
                        _local_user["user"] = demo_user
        return self.get_response(request)
