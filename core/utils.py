"""ابزارهای کمکی عمومی: اعداد فارسی، تاریخ شمسی، قالب‌بندی مبلغ."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import jdatetime
import datetime as _dt

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def fa(value) -> str:
    """تبدیل ارقام لاتین به فارسی."""
    return str(value).translate(FA_DIGITS)


def en(value) -> str:
    """تبدیل ارقام فارسی/عربی به لاتین (برای پردازش ورودی)."""
    return str(value).translate(EN_DIGITS)


def num(value, decimals: int = 0) -> str:
    """قالب‌بندی عدد با جداکننده‌ی هزارگان و ارقام فارسی."""
    if value in (None, ""):
        return "—"
    try:
        value = Decimal(str(value))
        q = Decimal(1).scaleb(-decimals)
        value = value.quantize(q, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        # مقدار خارج از محدودهٔ قابل نمایش (مثلاً سرریز) — همان‌طور نمایش داده می‌شود
        return fa(str(value))
    formatted = f"{value:,.{decimals}f}"
    return fa(formatted)


def money(toman, decimals: int = 0) -> str:
    """قالب‌بندی مبلغ تومانی به صورت خوانا: م.ت (میلیون تومان) / م.ی (میلیارد)."""
    if toman in (None, ""):
        return "—"
    value = Decimal(str(toman))
    billion = Decimal(1_000_000_000)
    million = Decimal(1_000_000)
    if abs(value) >= billion:
        return f"{num(value / billion, 2)} میلیارد"
    if abs(value) >= million:
        return f"{num(value / million, 0)} م.ت"
    return f"{num(value, 0)} ت"


def money_short(toman) -> str:
    """نسخه‌ی کوتاه برای جدول‌ها."""
    if toman in (None, ""):
        return "—"
    value = Decimal(str(toman))
    if abs(value) >= Decimal(1_000_000_000):
        return f"{num(value / Decimal(1_000_000_000), 2)} م.ی"
    if abs(value) >= Decimal(1_000_000):
        return f"{num(value / Decimal(1_000_000), 0)} م.ت"
    return num(value, 0)


def jalali(value, fmt: str = "%Y/%m/%d") -> str:
    """تاریخ میلادی → شمسی."""
    if not value:
        return "—"
    try:
        if isinstance(value, _dt.datetime):
            value = value.astimezone(_dt.timezone(_dt.timedelta(hours=3, minutes=30))).date()
        return fa(jdatetime.date.fromgregorian(date=value).strftime(fmt))
    except Exception:
        return fa(str(value))


def jalali_dt(value, fmt: str = "%Y/%m/%d %H:%M") -> str:
    """تاریخ و ساعت میلادی → شمسی."""
    if not value:
        return "—"
    try:
        if isinstance(value, _dt.datetime):
            local = value.astimezone(_dt.timezone(_dt.timedelta(hours=3, minutes=30)))
            j = jdatetime.datetime.fromgregorian(datetime=local)
        else:
            j = jdatetime.datetime.fromgregorian(date=value)
        return fa(j.strftime(fmt))
    except Exception:
        return fa(str(value))


def parse_jalali(text: str | None):
    """رشته‌ی شمسی (۱۴۰۵/۰۷/۰۱ یا 1405-7-1) → تاریخ میلادی. اگر شمسی نبود None."""
    if not text:
        return None
    cleaned = en(str(text)).strip().replace("-", "/").replace(".", "/")
    parts = [p for p in cleaned.split("/") if p.strip()]
    if len(parts) != 3:
        return None
    try:
        y, m, d = (int(p) for p in parts)
    except ValueError:
        return None
    try:
        if y > 1600:  # سال میلادی نوشته شده است
            return _dt.date(y, m, d)
        return jdatetime.date(y, m, d).togregorian()
    except ValueError:
        return None


def today_jalali() -> str:
    return fa(jdatetime.date.today().strftime("%Y/%m/%d"))


def days_until(value) -> int | None:
    """تعداد روز باقی‌مانده تا تاریخ (منفی = گذشته)."""
    if not value:
        return None
    from django.utils import timezone

    if hasattr(value, "date") and not isinstance(value, _dt.date):
        value = value.date()
    if isinstance(value, _dt.datetime):
        value = value.date()
    try:
        return (value - timezone.localdate()).days
    except TypeError:
        return None
