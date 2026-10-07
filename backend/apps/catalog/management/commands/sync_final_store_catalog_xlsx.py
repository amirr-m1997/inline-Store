from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.management.commands.import_catalog_xlsx import NS, XlsxReader
from apps.catalog.models import Category, Product
from apps.carts.models import CartItem
from apps.inventory.models import Inventory, Issue, Receipt, Reservation
from apps.rfq.models import RequestForQuotationItem, SalesQuotationItem


EXCLUDED_SHEETS = {"کل کالا", "نتیجه", "کالای ناقص"}
REQUIRED_COLUMNS = {"KALACODE", "SERIALNAME", "MOJODI", "VAHED"}


class Command(BaseCommand):
    help = "Synchronize the final, categorized store Excel file and optionally remove products outside it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=Path(__file__).resolve().parents[5] / "فایل نهایی تفکیک کالاها جهت درج در سایت فروش.xlsx",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--prune", action="store_true", help="Delete products not present in the final categorized sheets.")
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        source = options["source"]
        if not source.is_file():
            raise CommandError(f"Excel file does not exist: {source}")

        rows, sheets, blank_name_rows = self._read_rows(source)
        codes = set(rows)
        existing_by_code = {
            product.code: product
            for product in Product.objects.filter(code__in=codes).select_related("category")
        }
        outside = Product.objects.exclude(code__in=codes)
        report = {
            "source_sheet_count": len(sheets),
            "excel_unique_products": len(rows),
            "duplicate_sheet_rows": sum(len(items) - 1 for items in rows.values()),
            "rows_without_name": blank_name_rows,
            "database_products_before": Product.objects.count(),
            "matched_products": len(existing_by_code),
            "products_to_create": len(codes - set(existing_by_code)),
            "products_outside_excel": outside.count(),
            "inventory_receipts_outside_excel": Receipt.objects.filter(product__in=outside).count(),
            "inventory_issues_outside_excel": Issue.objects.filter(product__in=outside).count(),
            "inventory_reservations_outside_excel": Reservation.objects.filter(product__in=outside).count(),
            "cart_items_outside_excel": CartItem.objects.filter(product__in=outside).count(),
            "rfq_items_outside_excel": RequestForQuotationItem.objects.filter(product__in=outside).count(),
            "quotation_items_outside_excel": SalesQuotationItem.objects.filter(product__in=outside).count(),
        }

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(self._format_report(report)))
            return

        with transaction.atomic():
            category_by_sheet = self._categories_for_missing_rows(rows)
            created, updated = self._upsert_products(rows, existing_by_code, category_by_sheet, options["batch_size"])
            report["products_created"] = created
            report["products_updated"] = updated
            report["inventories_synced"] = self._sync_inventory(rows, options["batch_size"])

            if options["prune"]:
                # These relations intentionally protect products.  Once the user has chosen a
                # catalog replacement, their dependent inventory history is removed together.
                removable = Product.objects.exclude(code__in=codes)
                Reservation.objects.filter(product__in=removable).delete()
                Receipt.objects.filter(product__in=removable).delete()
                Issue.objects.filter(product__in=removable).delete()
                CartItem.objects.filter(product__in=removable).delete()
                # Quotations keep their snapshot fields. Detaching them preserves issued
                # documents while allowing their removed catalog products to be deleted.
                SalesQuotationItem.objects.filter(product__in=removable).update(product=None)
                RequestForQuotationItem.objects.filter(product__in=removable).delete()
                deleted, _ = removable.delete()
                report["deleted_rows_including_related"] = deleted
                report["products_after_sync"] = Product.objects.count()
            else:
                report["products_after_sync"] = Product.objects.count()

        self.stdout.write(self.style.SUCCESS(self._format_report(report)))

    def _read_rows(self, source):
        reader = XlsxReader(source)
        rows = {}
        blank_name_rows = 0
        selected_sheets = []
        for sheet in reader.sheets:
            if sheet in EXCLUDED_SHEETS:
                continue
            sheet_rows = self._stream_rows(reader, sheet)
            try:
                header = next(sheet_rows)
            except StopIteration:
                continue
            columns = {str(value).strip(): index for index, value in enumerate(header) if value}
            if not REQUIRED_COLUMNS.issubset(columns):
                continue
            selected_sheets.append(sheet)
            for row_number, row in enumerate(sheet_rows, start=2):
                code = self._value(row, columns["KALACODE"])
                if not code:
                    continue
                item = {
                    "code": code,
                    "name": self._value(row, columns["SERIALNAME"]),
                    "quantity": self._quantity(self._value(row, columns["MOJODI"]), sheet, row_number),
                    "unit": self._value(row, columns["VAHED"]) or "عدد",
                    "sheet": sheet,
                    "condition": Product.Condition.USED if sheet == "کارکرده" or "كاركرده" in self._value(row, columns["SERIALNAME"]) else Product.Condition.NEW,
                }
                if not item["name"]:
                    blank_name_rows += 1
                rows.setdefault(code, []).append(item)
        if not rows:
            raise CommandError("No valid product sheets were found in the Excel file.")
        return rows, selected_sheets, blank_name_rows

    @staticmethod
    def _stream_rows(reader, sheet):
        """Read only populated XML rows; workbook dimensions contain formatting up to row 1,048,576."""
        seen_content = False
        empty_streak = 0
        with reader.archive.open(reader.sheets[sheet]) as stream:
            for _, element in ElementTree.iterparse(stream, events=("end",)):
                if element.tag != f"{NS}row":
                    continue
                values = []
                for cell in element.findall(f"{NS}c"):
                    index = reader._column_index(cell.attrib.get("r", ""))
                    while len(values) <= index:
                        values.append("")
                    values[index] = reader._cell_value(cell)
                yield values
                element.clear()
                if any(values):
                    seen_content = True
                    empty_streak = 0
                elif seen_content:
                    empty_streak += 1
                    # The source has a million formatted, but empty, tail rows. Product
                    # rows are contiguous and a short blank run marks the true end.
                    if empty_streak >= 20:
                        break

    def _categories_for_missing_rows(self, rows):
        missing_sheets = {items[-1]["sheet"] for code, items in rows.items() if not Product.objects.filter(code=code).exists()}
        if not missing_sheets:
            return {}
        root, _ = Category.objects.get_or_create(
            parent=None,
            code="excel-final",
            defaults={"name_fa": "کالاهای تفکیک‌شده فروشگاه", "name_en": "", "slug": "excel-final-store", "is_active": True},
        )
        result = {}
        for sheet in sorted(missing_sheets):
            result[sheet], _ = Category.objects.get_or_create(
                parent=root,
                code=sheet,
                defaults={"name_fa": sheet, "name_en": "", "slug": "", "is_active": True},
            )
        return result

    def _upsert_products(self, rows, existing_by_code, category_by_sheet, batch_size):
        create, update = [], []
        for code, items in rows.items():
            item = items[-1]
            product = existing_by_code.get(code)
            if product is None:
                product = Product(
                    code=code,
                    name=item["name"] or code,
                    slug=f"catalog-{code}",
                    category=category_by_sheet[item["sheet"]],
                    unit=item["unit"],
                    condition=item["condition"],
                    is_active=True,
                )
                create.append(product)
            else:
                if item["name"]:
                    product.name = item["name"]
                product.unit = item["unit"]
                product.condition = item["condition"]
                product.is_active = True
                update.append(product)
        Product.objects.bulk_create(create, batch_size=batch_size)
        if update:
            Product.objects.bulk_update(update, ["name", "unit", "condition", "is_active", "updated_at"], batch_size=batch_size)
        return len(create), len(update)

    def _sync_inventory(self, rows, batch_size):
        quantities = {code: items[-1]["quantity"] for code, items in rows.items()}
        product_ids = dict(Product.objects.filter(code__in=quantities).values_list("code", "id"))
        current = {inventory.product_id: inventory for inventory in Inventory.objects.filter(product_id__in=product_ids.values())}
        create, update = [], []
        for code, product_id in product_ids.items():
            inventory = current.get(product_id)
            if inventory is None:
                create.append(Inventory(product_id=product_id, on_hand_quantity=quantities[code], reserved_quantity=0))
            else:
                inventory.on_hand_quantity = quantities[code]
                inventory.reserved_quantity = 0
                update.append(inventory)
        Inventory.objects.bulk_create(create, batch_size=batch_size)
        if update:
            Inventory.objects.bulk_update(update, ["on_hand_quantity", "reserved_quantity", "updated_at"], batch_size=batch_size)
        return len(create) + len(update)

    @staticmethod
    def _value(row, index):
        return str(row[index]).strip() if index < len(row) and row[index] not in (None, "") else ""

    @staticmethod
    def _quantity(value, sheet, row_number):
        try:
            quantity = Decimal(value or "0").quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as error:
            raise CommandError(f"Invalid inventory quantity in {sheet}, row {row_number}: {value}") from error
        if quantity < 0:
            raise CommandError(f"Inventory quantity must be non-negative in {sheet}, row {row_number}.")
        return quantity

    @staticmethod
    def _format_report(report):
        return "Final store catalog sync: " + ", ".join(f"{key}={value}" for key, value in report.items())
