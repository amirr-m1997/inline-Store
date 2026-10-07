"""کامپایل فایل‌های ترجمه‌ی .po به .mo بدون نیاز به بسته‌ی gettext.

در محیط تولید معمولاً دستور `django-admin compilemessages` (که به msgfmt نیاز دارد)
اجرا می‌شود؛ این دستور برای محیط‌هایی است که gettext نصب نیست و همان خروجی .mo
استاندارد را می‌سازد. فرمت .mo در این ماژول به‌صورت دستی نوشته می‌شود.

اجرا:
    python3 manage.py compile_po                 # همه‌ی locale/**/LC_MESSAGES/*.po
    python3 manage.py compile_po --check         # فقط بررسی می‌کند .moها به‌روز هستند
"""
from __future__ import annotations

import struct
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def parse_po(text: str) -> dict[str, str]:
    """تجزیه‌ی سادهٔ فایل .po — جفت‌های msgid/msgstr (بدون plural و بدون fuzzy)."""
    entries: dict[str, str] = {}
    msgid = msgstr = None
    state = None
    skip = False

    def flush():
        nonlocal msgid, msgstr, skip
        if msgid is not None and not skip:
            entries[msgid] = msgstr or ""
        msgid = msgstr = None
        skip = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            state = None
            continue
        if line.startswith("#"):
            if "fuzzy" in line:
                skip = True
            continue
        if line.startswith("msgid "):
            if msgid is not None:
                flush()
            msgid = _unquote(line[6:])
            state = "id"
        elif line.startswith("msgstr "):
            msgstr = _unquote(line[7:])
            state = "str"
        elif line.startswith('"'):
            chunk = _unquote(line)
            if state == "id":
                msgid = (msgid or "") + chunk
            elif state == "str":
                msgstr = (msgstr or "") + chunk
    flush()
    return entries


def _unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        value = value[1:-1]
    return value.encode("utf-8").decode("unicode_escape").encode("latin-1", "ignore").decode("utf-8") \
        if "\\" in value else value


def compile_mo(entries: dict[str, str]) -> bytes:
    """ساخت بایت‌های فایل .mo بر اساس ساختار GNU gettext (little-endian)."""
    items = sorted(entries.items(), key=lambda pair: pair[0].encode("utf-8"))
    count = len(items)

    header_size = 7 * 4
    ids_table = header_size
    strs_table = ids_table + count * 8
    data_start = strs_table + count * 8

    # نکته: ابتدا کل بلوک شناسه‌ها ساخته می‌شود تا آفست رشته‌ها درست محاسبه شود
    ids_blob = b""
    ids_index: list[tuple[int, int]] = []
    for msgid, _msgstr in items:
        raw = msgid.encode("utf-8") + b"\x00"
        ids_index.append((len(raw) - 1, data_start + len(ids_blob)))
        ids_blob += raw

    strs_start = data_start + len(ids_blob)
    strs_blob = b""
    strs_index: list[tuple[int, int]] = []
    for _msgid, msgstr in items:
        raw = msgstr.encode("utf-8") + b"\x00"
        strs_index.append((len(raw) - 1, strs_start + len(strs_blob)))
        strs_blob += raw

    out = struct.pack("<7I", 0x950412DE, 0, count, ids_table, strs_table, 0, 0)
    for length, offset in ids_index:
        out += struct.pack("<2I", length, offset)
    for length, offset in strs_index:
        out += struct.pack("<2I", length, offset)
    return out + ids_blob + strs_blob


class Command(BaseCommand):
    help = "کامپایل فایل‌های ترجمه (.po → .mo) بدون نیاز به msgfmt"

    def add_arguments(self, parser):
        parser.add_argument("--check", action="store_true",
                            help="فقط بررسی به‌روزبودن فایل‌های .mo")

    def handle(self, *args, **options):
        locale_dirs = list(getattr(settings, "LOCALE_PATHS", []))
        if not locale_dirs:
            locale_dirs = [Path(settings.BASE_DIR) / "locale"]

        compiled = skipped = 0
        for base in locale_dirs:
            for po_path in sorted(Path(base).glob("*/LC_MESSAGES/*.po")):
                mo_path = po_path.with_suffix(".mo")
                if options["check"]:
                    fresh = mo_path.exists() and mo_path.stat().st_mtime >= po_path.stat().st_mtime
                    style = self.style.SUCCESS if fresh else self.style.ERROR
                    self.stdout.write(style(f"{'به‌روز' if fresh else 'قدیمی'} — {po_path}"))
                    skipped += fresh
                    continue
                entries = parse_po(po_path.read_text(encoding="utf-8"))
                if not entries:
                    self.stdout.write(self.style.WARNING(f"هیچ translated entry در {po_path} نبود"))
                    continue
                mo_path.write_bytes(compile_mo(entries))
                compiled += 1
                self.stdout.write(self.style.SUCCESS(
                    f"{po_path} → {mo_path.name} ({len(entries)} رشته)"))

        if not options["check"]:
            self.stdout.write(self.style.SUCCESS(f"پایان: {compiled} فایل ترجمه کامپایل شد."))
        else:
            self.stdout.write(f"{skipped} فایل به‌روز بود.")
