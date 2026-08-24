from django import forms
from django.utils.html import format_html


class CategoryPickerWidget(forms.Select):
    """A compact category selector with a modal, level-by-level browser."""

    class Media:
        css = {"all": ("admin/catalog/category_picker.css",)}
        js = ("admin/catalog/category_picker.js",)

    def __init__(self, *args, picker_url, allow_empty=False, exclude_ids=(), **kwargs):
        self.picker_url = picker_url
        self.allow_empty = allow_empty
        self.exclude_ids = tuple(sorted({int(value) for value in exclude_ids}))
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        select_attrs = {**(attrs or {})}
        select_attrs["class"] = f"{select_attrs.get('class', '')} category-picker__select".strip()
        select_html = super().render(name, value, select_attrs, renderer)
        clear_button = ""
        if self.allow_empty:
            clear_button = format_html(
                '<button type="button" class="category-picker__clear" data-category-picker-clear>بدون والد</button>'
            )
        return format_html(
            '<div class="category-picker" data-category-picker data-picker-url="{}" '
            'data-exclude-ids="{}" data-allow-empty="{}">{}'
            '<div class="category-picker__value" data-category-picker-value></div>'
            '<button type="button" class="button" data-category-picker-open>انتخاب از دسته‌بندی‌ها</button>{}'
            '</div>',
            self.picker_url,
            ",".join(str(value) for value in self.exclude_ids),
            str(self.allow_empty).lower(),
            select_html,
            clear_button,
        )