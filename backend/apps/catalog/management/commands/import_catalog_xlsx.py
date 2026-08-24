import re
import zipfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory


MAIN_SHEET = "کالاها"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class XlsxReader:
    def __init__(self, source):
        self.source = source
        self.archive = zipfile.ZipFile(source)
        self.shared_strings = self._read_shared_strings()
        self.sheets = self._read_sheets()

    def _read_shared_strings(self):
        if "xl/sharedStrings.xml" not in self.archive.namelist():
            return []
        root = ElementTree.fromstring(self.archive.read("xl/sharedStrings.xml"))
        return ["".join(node.text or "" for node in item.iter(f"{NS}t")) for item in root.findall(f"{NS}si")]

    def _read_sheets(self):
        workbook = ElementTree.fromstring(self.archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(self.archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets = {}
        for sheet in workbook.find(f"{NS}sheets"):
            rel_id = sheet.attrib[f"{REL_NS}id"]
            sheets[sheet.attrib["name"]] = "xl/" + targets[rel_id]
        return sheets

    def rows(self, sheet_name):
        if sheet_name not in self.sheets:
            raise CommandError(f"Sheet not found in Excel file: {sheet_name}")
        root = ElementTree.fromstring(self.archive.read(self.sheets[sheet_name]))
        for row in root.iter(f"{NS}row"):
            values = []
            for cell in row.findall(f"{NS}c"):
                index = self._column_index(cell.attrib.get("r", ""))
                while len(values) <= index:
                    values.append("")
                values[index] = self._cell_value(cell)
            yield values

    @staticmethod
    def _column_index(reference):
        match = re.match(r"([A-Z]+)", reference)
        result = 0
        for char in match.group(1) if match else "":
            result = result * 26 + ord(char) - 64
        return result - 1

    def _cell_value(self, cell):
        data_type = cell.attrib.get("t")
        if data_type == "inlineStr":
            return "".join(node.text or "" for node in cell.iter(f"{NS}t")).strip()
        value = cell.find(f"{NS}v")
        if value is None:
            return ""
        raw = (value.text or "").strip()
        if data_type == "s":
            return self.shared_strings[int(raw)].strip()
        return raw


class Command(BaseCommand):
    help = "Imports product catalog rows from the complete categorized Excel file."

    required_columns = {
        "کد کالا",
        "نام کالا",
        "واحد",
        "موجودی",
        "کد دسته اصلی (t)",
        "دسته اصلی",
        "کد گروه (g)",
        "گروه",
        "کد زیر دسته (z)",
        "زیر دسته",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=Path(__file__).resolve().parents[5] / "کالاها_با_دسته_بندی_کامل.xlsx",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        source = options["source"]
        if not source.is_file():
            raise CommandError(f"Excel file does not exist: {source}")

        reader = XlsxReader(source)
        rows = list(self._product_rows(reader))
        report = {
            "excel_rows": len(rows),
            "categories_created": 0,
            "categories_updated": 0,
            "products_created": 0,
            "products_updated": 0,
            "inventories_created": 0,
            "inventories_updated": 0,
            "skipped_rows": 0,
        }

        with transaction.atomic():
            categories = self._import_categories(rows, report)
            self._import_products(rows, categories, report, options["batch_size"])
            if options["dry_run"]:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("Catalog Excel import: " + ", ".join(f"{key}={value}" for key, value in report.items())))

    def _product_rows(self, reader):
        rows = iter(reader.rows(MAIN_SHEET))
        try:
            header = next(rows)
        except StopIteration as error:
            raise CommandError("The products sheet is empty.") from error
        columns = {name: index for index, name in enumerate(header)}
        missing = sorted(self.required_columns - set(columns))
        if missing:
            raise CommandError("Missing required Excel columns: " + ", ".join(missing))

        seen_codes = set()
        for row_number, row in enumerate(rows, start=2):
            item = {name: self._value(row, index) for name, index in columns.items()}
            code = item["کد کالا"]
            if not code:
                continue
            if code in seen_codes:
                raise CommandError(f"Duplicate product code in Excel row {row_number}: {code}")
            seen_codes.add(code)
            item["_row_number"] = row_number
            yield item

    def _import_categories(self, rows, report):
        categories = {}
        for item in rows:
            root_key = (None, item["کد دسته اصلی (t)"])
            root = categories.get(root_key) or self._category(
                None,
                item["کد دسته اصلی (t)"],
                item["دسته اصلی"],
                f"type-{item['کد دسته اصلی (t)']}",
                report,
            )
            categories[root_key] = root

            group_key = (root.pk, item["کد گروه (g)"])
            group = categories.get(group_key) or self._category(
                root,
                item["کد گروه (g)"],
                item["گروه"],
                f"type-{item['کد دسته اصلی (t)']}-group-{item['کد گروه (g)']}",
                report,
            )
            categories[group_key] = group

            subgroup_key = (item["کد دسته اصلی (t)"], item["کد گروه (g)"], item["کد زیر دسته (z)"])
            subgroup = categories.get(subgroup_key) or self._category(
                group,
                item["کد زیر دسته (z)"],
                item["زیر دسته"],
                f"type-{item['کد دسته اصلی (t)']}-group-{item['کد گروه (g)']}-subgroup-{item['کد زیر دسته (z)']}",
                report,
            )
            categories[subgroup_key] = subgroup
        return categories

    def _category(self, parent, code, name, slug, report):
        if not code or not name:
            raise CommandError("A category path is incomplete in the Excel file.")
        category, created = Category.objects.update_or_create(
            parent=parent,
            code=code,
            defaults={"name_fa": name, "name_en": "", "slug": slug, "is_active": True},
        )
        report["categories_created" if created else "categories_updated"] += 1
        return category

    def _import_products(self, rows, categories, report, batch_size):
        existing = {product.code: product for product in Product.objects.filter(code__in=[item["کد کالا"] for item in rows])}
        to_create = []
        to_update = []
        inventory_by_code = {}

        for item in rows:
            category = categories.get((item["کد دسته اصلی (t)"], item["کد گروه (g)"], item["کد زیر دسته (z)"]))
            if category is None:
                raise CommandError(f"Product {item['کد کالا']} has no matching category path.")
            quantity = self._quantity(item["موجودی"], item["_row_number"])
            code = item["کد کالا"]
            product = existing.get(code)
            if product is None:
                product = Product(
                    code=code,
                    name=item["نام کالا"],
                    slug=f"catalog-{code}",
                    category=category,
                    unit=item["واحد"],
                    is_active=True,
                )
                to_create.append(product)
            else:
                product.name = item["نام کالا"]
                product.category = category
                product.unit = item["واحد"]
                product.is_active = True
                to_update.append(product)
            inventory_by_code[code] = quantity

        Product.objects.bulk_create(to_create, batch_size=batch_size)
        if to_update:
            Product.objects.bulk_update(to_update, ["name", "category", "unit", "is_active", "updated_at"], batch_size=batch_size)
        report["products_created"] = len(to_create)
        report["products_updated"] = len(to_update)

        products = Product.objects.filter(code__in=inventory_by_code).only("id", "code")
        existing_inventory = {inventory.product_id: inventory for inventory in Inventory.objects.filter(product__code__in=inventory_by_code)}
        create_inventory = []
        update_inventory = []
        for product in products:
            quantity = inventory_by_code[product.code]
            inventory = existing_inventory.get(product.id)
            if inventory is None:
                create_inventory.append(Inventory(product=product, on_hand_quantity=quantity, reserved_quantity=0))
            else:
                inventory.on_hand_quantity = quantity
                inventory.reserved_quantity = 0
                update_inventory.append(inventory)
        Inventory.objects.bulk_create(create_inventory, batch_size=batch_size)
        if update_inventory:
            Inventory.objects.bulk_update(update_inventory, ["on_hand_quantity", "reserved_quantity", "updated_at"], batch_size=batch_size)
        report["inventories_created"] = len(create_inventory)
        report["inventories_updated"] = len(update_inventory)

    @staticmethod
    def _value(row, index):
        return row[index].strip() if index < len(row) and row[index] else ""

    @staticmethod
    def _quantity(value, row_number):
        try:
            number = Decimal(value or "0").quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as error:
            raise CommandError(f"Invalid inventory quantity in Excel row {row_number}: {value}") from error
        if number < 0:
            raise CommandError(f"Inventory quantity must be a non-negative number in Excel row {row_number}: {value}")
        return number
