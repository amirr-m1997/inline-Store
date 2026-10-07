"""دسترس‌بندی مسیرهای سفارشی پنل.

`admin.site.admin_view` فقط «کارمند بودن» را می‌سنجد؛ برای مسیرهایی که داده‌ی
مالی/فروش نشان می‌دهند یا چیزی می‌نویسند، باید مجوز مدل هم بررسی شود. این
دکوراتور همان کار را می‌کند و در صورت نبود مجوز، ۴۰۳ برمی‌گرداند.
"""
from __future__ import annotations

from functools import wraps

from django.core.exceptions import PermissionDenied


def any_perm(*codenames: str):
    """اجازه فقط اگر کاربر دست‌کم یکی از مجوزهای نام‌برده را داشته باشد."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not user.is_authenticated:
                raise PermissionDenied
            if not any(user.has_perm(code) for code in codenames):
                raise PermissionDenied(
                    "برای این بخش به مجوز دسترسی نیاز دارید: " + "، ".join(codenames)
                )
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
