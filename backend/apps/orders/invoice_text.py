"""Persian presentation helpers for the official A4 invoice document.

Everything here is dependency-free on purpose: the invoice must render on any
deployment (SQLite dev, Postgres prod) without extra system packages.
"""
from __future__ import annotations

from datetime import datetime

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def _fa_chars(text: str) -> str:
    return "".join(FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in text)


def fa_digits(value) -> str:
    """Render an integer with Persian digits and ٬ thousand separators."""
    return _fa_chars(f"{int(value):,}".replace(",", "٬"))


_ONES = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه", "ده",
         "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده"]
_TENS = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
_HUNDREDS = ["", "یکصد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
_SCALES = [(10 ** 9, "میلیارد"), (10 ** 6, "میلیون"), (10 ** 3, "هزار")]


def _three_digits(number: int) -> str:
    parts = []
    hundreds, rest = divmod(number, 100)
    if hundreds:
        parts.append(_HUNDREDS[hundreds])
    if rest:
        if rest < 20:
            parts.append(_ONES[rest])
        else:
            tens, ones = divmod(rest, 10)
            parts.append(_TENS[tens] + (f" و {_ONES[ones]}" if ones else ""))
    return " و ".join(parts)


def amount_in_words(value) -> str:
    """Spell a Rial/Toman integer amount in Persian words."""
    number = int(value)
    if number == 0:
        return "صفر"
    if number < 0:
        return "منفی " + amount_in_words(-number)
    parts = []
    for scale, name in _SCALES:
        chunk, number = divmod(number, scale)
        if chunk:
            parts.append(f"{_three_digits(chunk)} {name}")
    if number:
        parts.append(_three_digits(number))
    return " و ".join(parts)


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert a Gregorian date to (jy, jm, jd). Proleptic, no dependencies."""
    g_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + g_days[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def fa_date(value: datetime | None) -> str:
    if not value:
        return "—"
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{_fa_chars(str(jy))}/{_fa_chars(f'{jm:02d}')}/{_fa_chars(f'{jd:02d}')}"


def fa_time(value: datetime | None) -> str:
    if not value:
        return "—"
    return _fa_chars(value.strftime("%H:%M:%S"))
