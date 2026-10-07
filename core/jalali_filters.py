"""فیلترهای تاریخ شمسی برای پنل ادمین مهراصل.

پنل همه‌جا تاریخ را شمسی نشان می‌دهد (ستون‌های فهرست، داشبورد، گزارش‌ها) اما
فیلتر بازه‌ی تاریخِ پیش‌فرض (unfold.contrib.filters.admin.RangeDateFilter) فقط
ورودی میلادی «YYYY-MM-DD» می‌پذیرفت. نتیجه: کاربر فارسی‌زبان برای فیلتر کردن
فهرست سفارش‌ها باید تاریخ را میلادی وارد می‌کرد؛ اگر «۱۴۰۵/۰۷/۱۵» تایپ می‌شد،
unfold آن را نامعتبر می‌دانست و بی‌صدا فیلتری اعمال نمی‌شد.

این ماژول همان فیلتر را با سه تغییر ارائه می‌دهد:

۱. ورودی شمسی را می‌پذیرد: «۱۴۰۵/۰۷/۱۵»، «1405-7-15»، «1405.07.15»، «14050715».
۲. ورودی میلادی را هم دست‌نخورده می‌پذیرد (سازگاری با رفتار قبلی).
۳. مقدار فعلی فیلتر را شمسی نشان می‌دهد (هم‌خوان با ستون‌های فهرست).

راه‌اندازی در ادمین:

    from core.jalali_filters import JalaliRangeDateFilter as RangeDateFilter
    list_filter = [("ordered_at", RangeDateFilter), ...]
"""
from __future__ import annotations

import datetime as _dt
from typing import Iterator

from django import forms
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.contrib.filters.forms import RangeDateForm
from unfold.widgets import INPUT_CLASSES

from .utils import en, fa, jalali, parse_jalali

EMPTY_VALUES = (None, "", [], (), {})


def to_gregorian(value) -> _dt.date | None:
    """ورودی کاربر (شمسی یا میلادی) → تاریخ میلادی؛ None اگر نامعتبر باشد."""
    if value in EMPTY_VALUES:
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value

    text = en(str(value)).strip()
    if not text:
        return None

    # ۱۴۰۵۰۷۱۵ یا 20260405 (بدون جداکننده)
    if len(text) == 8 and text.isdigit():
        text = f"{text[:4]}/{text[4:6]}/{text[6:]}"

    text = text.replace("-", "/").replace(".", "/").replace("\\", "/")
    return parse_jalali(text)


class JalaliDateField(forms.DateField):
    """فیلد تاریخ که ورودی شمسی را هم می‌فهمد."""

    def to_python(self, value):
        if value in self.empty_values:
            return None
        parsed = to_gregorian(value)
        if parsed is None:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
        return parsed


class JalaliRangeDateForm(RangeDateForm):
    """نسخه‌ی شمسیِ فرم بازه‌ی تاریخ؛ با راهنمای قالب در placeholder و title."""

    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(name, *args, **kwargs)
        for key, label in ((f"{name}_from", "از تاریخ"), (f"{name}_to", "تا تاریخ")):
            self.fields[key] = JalaliDateField(
                label="",
                required=False,
                widget=forms.DateInput(
                    attrs={
                        "placeholder": "۱۴۰۵/۰۷/۱۵",
                        "title": f"{label} — قالب شمسی: ۱۴۰۵/۰۷/۱۵ (میلادی هم پذیرفته می‌شود)",
                        "class": "vDateField " + " ".join(INPUT_CLASSES),
                        "inputmode": "numeric",
                        "autocomplete": "off",
                    }
                ),
            )


class JalaliRangeDateFilter(RangeDateFilter):
    """فیلتر بازه‌ی تاریخ با ورودی و نمایش شمسی."""

    form_class = JalaliRangeDateForm

    def _raw(self, side: str):
        return self.used_parameters.get(f"{self.parameter_name}_{side}")

    def _bound(self, parsed: _dt.date, side: str):
        """تاریخ روز → مقدار مقایسه‌ای؛ برای فیلدهای زمان‌دار، ابتدا/انتهای روز به وقت تهران."""
        from django.db import models as dj_models
        from django.utils import timezone

        if isinstance(self.field, dj_models.DateTimeField):
            moment = (
                _dt.datetime.combine(parsed, _dt.time.min)
                if side == "from"
                else _dt.datetime.combine(parsed, _dt.time.max)
            )
            if timezone.is_naive(moment):
                moment = timezone.make_aware(moment, timezone.get_current_timezone())
            return moment
        return parsed

    def queryset(self, request, queryset):
        filters = {}
        for side, lookup in (("from", "gte"), ("to", "lte")):
            raw = self._raw(side)
            if raw in EMPTY_VALUES:
                continue
            parsed = to_gregorian(raw)
            if parsed is None:
                # ورودی نامعتبر: فیلتر اعمال نمی‌شود (رفتار پیش‌فرض unfold هم همین بود)
                continue
            filters[f"{self.parameter_name}__{lookup}"] = self._bound(parsed, side)
        if not filters:
            return queryset
        try:
            return queryset.filter(**filters)
        except (ValueError, TypeError):
            return None

    def choices(self, changelist) -> Iterator[dict]:
        data = {}
        for side in ("from", "to"):
            raw = self._raw(side)
            parsed = to_gregorian(raw)
            data[f"{self.parameter_name}_{side}"] = fa(jalali(parsed)) if parsed else (raw or None)

        yield {
            "request": self.request,
            "parameter_name": self.parameter_name,
            "form": self.form_class(name=self.parameter_name, data=data),
        }
