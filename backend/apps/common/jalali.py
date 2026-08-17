"""Small dependency-free Gregorian/Jalali presentation helpers.

Database timestamps remain timezone-aware Gregorian values.  These helpers are
for Persian admin/document/API presentation only.
"""

from datetime import date, datetime

from django.utils import timezone


def gregorian_to_jalali(year, month, day):
    """Convert a Gregorian date to a Jalali date tuple."""
    g_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy = year - 1600
    jy = 979
    days = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    days += day - 1 + g_days[month - 1]
    if month > 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        days += 1
    # The Gregorian epoch offset for the 1600-based calculation.
    days -= 79
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    jm = 1 + days // 31 if days < 186 else 7 + (days - 186) // 30
    jd = 1 + (days % 31 if days < 186 else (days - 186) % 30)
    return jy, jm, jd


def format_jalali(value, with_time=False, persian_digits=True):
    if value is None:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        parts = (*gregorian_to_jalali(value.year, value.month, value.day), value.hour, value.minute)
    elif isinstance(value, date):
        parts = (*gregorian_to_jalali(value.year, value.month, value.day), 0, 0)
    else:
        raise TypeError("format_jalali expects a date or datetime")
    result = f"{parts[0]:04d}/{parts[1]:02d}/{parts[2]:02d}"
    if with_time and isinstance(value, datetime):
        result += f" {parts[3]:02d}:{parts[4]:02d}"
    return result.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")) if persian_digits else result


def format_document_date(value, locale="fa", with_time=False):
    if locale == "en":
        if isinstance(value, datetime):
            value = timezone.localtime(value) if timezone.is_aware(value) else value
            return value.strftime("%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d")
        return value.strftime("%Y-%m-%d") if value else ""
    return format_jalali(value, with_time=with_time)
