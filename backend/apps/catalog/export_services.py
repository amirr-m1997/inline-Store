import html
import io
import re
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from apps.common.jalali import format_jalali


def clean_html_description(html_content):
    """
    Convert rich HTML description from CKEditor into clean, readable plain text.
    Preserves paragraph breaks, list bullets, and table structure while removing all HTML tags.
    """
    if not html_content:
        return ""
    # Convert paragraph, header, and list item breaks to newlines
    text = re.sub(r"<(br|p|div|tr|h[1-6])[^>]*>", "\n", str(html_content), flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities (&nbsp;, &zwnj;, &amp;, etc.)
    text = html.unescape(text)
    # Replace non-breaking spaces with standard space
    text = text.replace("\xa0", " ")
    # Clean up whitespace per line while preserving linebreaks
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned_lines = []
    empty_streak = 0
    for line in lines:
        if not line:
            empty_streak += 1
            if empty_streak <= 1:
                cleaned_lines.append("")
        else:
            empty_streak = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def estimate_pages_and_stats(plain_text):
    """
    Estimate words, characters, and standard book/document pages (approx 300 words / 1500 chars per page).
    """
    if not plain_text:
        return 0, 0, 0, "فاقد توضیحات"
    char_count = len(plain_text)
    word_count = len(plain_text.split())
    # Estimate standard A4/book page (approx 280-300 Persian words or 1400-1500 characters)
    pages = max(1, round(char_count / 1400)) if char_count > 0 else 0
    if pages <= 1:
        summary_label = f"۱ صفحه ({word_count:,} کلمه)"
    else:
        summary_label = f"{pages} صفحه (~{word_count:,} کلمه)"
    return pages, word_count, char_count, summary_label


def chunk_text_safely(text, max_chunk_size=25000):
    """
    Split text into chunks smaller than Excel's 32,767 character cell limit.
    Tries to split at newline or space boundaries.
    """
    if not text:
        return []
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    current_text = text
    while len(current_text) > max_chunk_size:
        split_pos = current_text.rfind("\n", 0, max_chunk_size)
        if split_pos < max_chunk_size * 0.7:
            split_pos = current_text.rfind(" ", 0, max_chunk_size)
        if split_pos < max_chunk_size * 0.5:
            split_pos = max_chunk_size
        chunks.append(current_text[:split_pos].strip())
        current_text = current_text[split_pos:].strip()
    if current_text:
        chunks.append(current_text)
    return chunks


def category_path_label(category):
    if not category:
        return "بدون دسته‌بندی"
    parts = []
    cursor = category
    while cursor is not None:
        parts.append(cursor.name_fa)
        cursor = cursor.parent
    return " / ".join(reversed(parts))


def build_products_excel_workbook(queryset):
    """
    Build a comprehensive, multi-sheet, beautifully styled .xlsx workbook
    specifically designed as a robust backup of products. Handles multi-page
    descriptions gracefully and losslessly.
    """
    workbook = Workbook()
    workbook.remove(workbook.active)  # Remove default sheet

    header_fill = PatternFill("solid", fgColor="0D5C63")
    sub_header_fill = PatternFill("solid", fgColor="177B82")
    zebra_fill = PatternFill("solid", fgColor="F7FAFA")
    header_font = Font(name="Tahoma", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Tahoma", size=9)
    bold_data_font = Font(name="Tahoma", size=9, bold=True)
    thin_border_side = Side(style="thin", color="E2E8F0")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # Sheet 1: Main product overview
    ws_main = workbook.create_sheet(title="فهرست و مشخصات محصولات")
    ws_main.sheet_view.rightToLeft = True
    ws_main.freeze_panes = "C2"

    main_headers = [
        ("ردیف", 8),
        ("کد کالا", 18),
        ("نام محصول", 40),
        ("دسته‌بندی", 32),
        ("برند", 20),
        ("وضعیت کالا", 14),
        ("واحد سنجش", 12),
        ("موجودی کل", 14),
        ("موجودی رزرو", 14),
        ("آخرین قیمت (ریال)", 18),
        ("درصد تخفیف", 12),
        ("وضعیت فعال", 12),
        ("نوع نمایش کاتالوگ", 18),
        ("تاریخ ثبت (شمسی)", 16),
        ("آخرین ویرایش (شمسی)", 20),
        ("حجم توضیحات", 22),
        ("خلاصه توضیحات", 50),
        ("متن کامل توضیحات (ایمن‌شده)", 60),
        ("مشخصات فنی", 40),
    ]

    ws_main.append([h[0] for h in main_headers])
    for col_idx, (title, width) in enumerate(main_headers, start=1):
        cell = ws_main.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws_main.column_dimensions[get_column_letter(col_idx)].width = width
    ws_main.row_dimensions[1].height = 28

    # Sheet 2: Dedicated multi-page / long descriptions sheet (lossless backup)
    ws_long = workbook.create_sheet(title="توضیحات طولانی و کامل")
    ws_long.sheet_view.rightToLeft = True
    ws_long.freeze_panes = "C2"

    long_headers = [
        ("کد کالا", 18),
        ("نام کالا", 35),
        ("شماره بخش / صفحه", 18),
        ("برآورد صفحات", 16),
        ("طول کاراکتر بخش", 16),
        ("متن بخش (خوانا)", 80),
        ("کد HTML خام بخش", 80),
    ]
    ws_long.append([h[0] for h in long_headers])
    for col_idx, (title, width) in enumerate(long_headers, start=1):
        cell = ws_long.cell(row=1, column=col_idx)
        cell.fill = sub_header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_long.column_dimensions[get_column_letter(col_idx)].width = width
    ws_long.row_dimensions[1].height = 28

    # Query optimization: prefetch prices and select related models
    optimized_qs = queryset.select_related("category", "brand", "inventory").prefetch_related("prices").order_by("-updated_at", "-id")

    row_number = 0
    long_desc_row_count = 0

    for product in optimized_qs:
        row_number += 1
        current_row = row_number + 1  # 1-indexed, row 1 is header

        # Inventory
        inv = getattr(product, "inventory", None)
        stock_qty = inv.on_hand_quantity if inv else 0
        reserved_qty = inv.reserved_quantity if inv else 0

        # Latest Price
        prices = list(product.prices.all())
        latest_price = prices[0].amount if prices else 0
        discount_pct = prices[0].discount_percentage if prices else 0

        # Catalog state
        display_status_parts = []
        if product.is_featured:
            display_status_parts.append("محصول منتخب")
        if product.is_obsolete:
            display_status_parts.append("منسوخ‌شده")
        if not display_status_parts:
            display_status_parts.append("عادی")
        catalog_state = " - ".join(display_status_parts)

        # Dates
        created_shamsi = format_jalali(product.created_at, with_time=False, persian_digits=False)
        updated_shamsi = format_jalali(product.updated_at, with_time=True, persian_digits=False)

        # Multi-page description processing
        raw_desc = product.description or ""
        clean_text = clean_html_description(raw_desc)
        pages, words, chars, pages_label = estimate_pages_and_stats(clean_text)

        # Summary for quick scanning (max 350 chars)
        summary = (clean_text[:350] + "...") if len(clean_text) > 350 else clean_text

        # Safe Excel cell text (cap at 30,000 characters to prevent Excel crash)
        if len(clean_text) > 30000:
            main_cell_desc = (
                clean_text[:30000]
                + "\n\n[توجه: ادامه توضیحات به دلیل محدودیت حجم سلول اکسل در برگه دوم «توضیحات طولانی و کامل» ثبت شده است]"
            )
        else:
            main_cell_desc = clean_text

        # Technical specs string
        specs_str = ""
        if isinstance(product.technical_specs, dict) and product.technical_specs:
            specs_str = "\n".join(f"{k}: {v}" for k, v in product.technical_specs.items())

        row_values = [
            row_number,
            product.code,
            product.name,
            category_path_label(product.category),
            product.brand.name if product.brand else "—",
            product.get_condition_display() if hasattr(product, "get_condition_display") else product.condition,
            product.unit,
            stock_qty,
            reserved_qty,
            latest_price,
            discount_pct,
            "فعال" if product.is_active else "غیرفعال",
            catalog_state,
            created_shamsi,
            updated_shamsi,
            pages_label,
            summary,
            main_cell_desc,
            specs_str,
        ]

        ws_main.append(row_values)
        ws_main.row_dimensions[current_row].height = 24  # Standard readable row height

        # Apply cell styling and number formats
        is_even = (row_number % 2 == 0)
        for col_idx in range(1, len(row_values) + 1):
            cell = ws_main.cell(row=current_row, column=col_idx)
            cell.font = data_font
            cell.border = cell_border
            if is_even:
                cell.fill = zebra_fill

            # Alignments and number formats
            if col_idx in (1, 6, 12, 13, 14, 15, 16):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (2, 7, 8, 9, 10, 11):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="top", wrap_text=True)

            if col_idx in (8, 9):
                cell.number_format = '#,##0'
            elif col_idx == 10:
                cell.number_format = '#,##0'
            elif col_idx == 11:
                cell.number_format = '0"%"'

        # If product has long or multi-page descriptions (> 800 chars or > 1 page),
        # also populate Sheet 2 with section-by-section breakdown and raw HTML backup
        if chars > 800 or len(raw_desc) > 800:
            text_chunks = chunk_text_safely(clean_text, max_chunk_size=25000)
            html_chunks = chunk_text_safely(raw_desc, max_chunk_size=25000)
            max_chunks = max(len(text_chunks), len(html_chunks), 1)

            for chunk_idx in range(max_chunks):
                long_desc_row_count += 1
                sec_text = text_chunks[chunk_idx] if chunk_idx < len(text_chunks) else ""
                sec_html = html_chunks[chunk_idx] if chunk_idx < len(html_chunks) else ""
                section_label = f"بخش {chunk_idx + 1} از {max_chunks}" if max_chunks > 1 else "متن کامل"

                ws_long.append([
                    product.code,
                    product.name,
                    section_label,
                    pages_label,
                    len(sec_text),
                    sec_text,
                    sec_html,
                ])
                long_row = long_desc_row_count + 1
                ws_long.row_dimensions[long_row].height = 24
                for c_idx in range(1, 8):
                    c = ws_long.cell(row=long_row, column=c_idx)
                    c.font = data_font
                    c.border = cell_border
                    c.alignment = Alignment(horizontal="right", vertical="top", wrap_text=True)

    # Set auto filters
    ws_main.auto_filter.ref = ws_main.dimensions
    if long_desc_row_count > 0:
        ws_long.auto_filter.ref = ws_long.dimensions

    return workbook


def export_products_to_excel_response(queryset, filename_prefix="backup_products"):
    """
    Export the given queryset of products to an HTTP Excel response with Jalali timestamp in filename.
    """
    workbook = build_products_excel_workbook(queryset)
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    now_jalali = format_jalali(timezone.now(), with_time=True, persian_digits=False).replace("/", "-").replace(" ", "_").replace(":", "-")
    ascii_filename = f"{filename_prefix}_{now_jalali}.xlsx"
    utf8_filename = f"پشتیبان_محصولات_{now_jalali}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # Support both ASCII fallback and RFC 5987 UTF-8 encoded Persian filenames
    encoded_filename = quote(utf8_filename)
    response["Content-Disposition"] = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    return response
