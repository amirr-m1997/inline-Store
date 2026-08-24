import re
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max

from apps.catalog.models import Product, ProductImage


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".jfif"}


class Command(BaseCommand):
    help = (
        "Links existing files in MEDIA_ROOT/products to products whose Product.code "
        "matches the image filename, allowing numeric suffixes such as _1 and _2."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=Path(settings.MEDIA_ROOT) / "products",
            help="Directory below MEDIA_ROOT containing product images (default: MEDIA_ROOT/products).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the import report without changing ProductImage records.",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Also link images to inactive products. By default those images are reported but skipped.",
        )

    def handle(self, *args, **options):
        source = options["source"].resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if not source.is_dir():
            raise CommandError(f"Image source directory does not exist: {source}")
        try:
            source.relative_to(media_root)
        except ValueError as error:
            raise CommandError("--source must be inside MEDIA_ROOT so file paths remain safe.") from error

        files, ignored = self._image_files(source)
        codes = {self._product_code_from_file(file) for file in files}
        products = Product.objects.in_bulk(codes, field_name="code")
        by_code = defaultdict(list)
        for file in files:
            by_code[self._product_code_from_file(file)].append(file)

        unmatched_codes = sorted(code for code in by_code if code not in products)
        inactive_codes = sorted(code for code, product in products.items() if not product.is_active)
        if not options["include_inactive"]:
            eligible_codes = set(products).difference(inactive_codes)
        else:
            eligible_codes = set(products)

        candidates = []
        for code in sorted(eligible_codes):
            for file in sorted(by_code[code]):
                relative = file.relative_to(media_root).as_posix()
                candidates.append((products[code], relative))

        existing_paths = set(
            ProductImage.objects.filter(image__in=[path for _, path in candidates]).values_list("image", flat=True)
        )
        new_candidates = [(product, path) for product, path in candidates if path not in existing_paths]

        report = {
            "image_files": len(files),
            "ignored_files": ignored,
            "matched_files": len(candidates),
            "unmatched_files": sum(len(by_code[code]) for code in unmatched_codes),
            "inactive_files_skipped": sum(len(by_code[code]) for code in inactive_codes if code not in eligible_codes),
            "already_linked": len(candidates) - len(new_candidates),
            "to_create": len(new_candidates),
        }
        self.stdout.write("Product image import report: " + ", ".join(f"{key}={value}" for key, value in report.items()))
        self._write_samples("Unmatched product codes", unmatched_codes)
        self._write_samples("Inactive product codes skipped", [code for code in inactive_codes if code not in eligible_codes])

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run complete: no ProductImage records were changed."))
            return

        created = self._create_images(new_candidates)
        self.stdout.write(self.style.SUCCESS(f"Imported {created} ProductImage record(s). Existing files were not moved or changed."))

    @staticmethod
    def _image_files(source):
        files = []
        ignored = 0
        for file in source.rglob("*"):
            if not file.is_file():
                continue
            if file.suffix.lower() not in IMAGE_EXTENSIONS:
                ignored += 1
                continue
            if not file.stem:
                ignored += 1
                continue
            files.append(file)
        return files, ignored

    @staticmethod
    def _product_code_from_file(file):
        return re.sub(r"_[0-9]+$", "", file.stem).strip()

    def _write_samples(self, label, values):
        if not values:
            return
        preview = ", ".join(values[:20])
        suffix = " ..." if len(values) > 20 else ""
        self.stdout.write(self.style.WARNING(f"{label} ({len(values)}): {preview}{suffix}"))

    @staticmethod
    def _create_images(candidates):
        if not candidates:
            return 0
        product_ids = {product.id for product, _ in candidates}
        images_by_product = defaultdict(list)
        for product, path in candidates:
            images_by_product[product.id].append((product, path))

        with transaction.atomic():
            existing_product_ids = set(
                ProductImage.objects.filter(product_id__in=product_ids).values_list("product_id", flat=True)
            )
            max_sort_orders = {
                row["product_id"]: row["max_sort_order"]
                for row in ProductImage.objects.filter(product_id__in=product_ids)
                .values("product_id")
                .annotate(max_sort_order=Max("sort_order"))
            }
            new_images = []
            for product_id in sorted(images_by_product):
                sort_order = (max_sort_orders.get(product_id) or -1) + 1
                has_existing_image = product_id in existing_product_ids
                for index, (product, path) in enumerate(images_by_product[product_id]):
                    new_images.append(
                        ProductImage(
                            product=product,
                            image=path,
                            is_primary=not has_existing_image and index == 0,
                            sort_order=sort_order + index,
                        )
                    )
            ProductImage.objects.bulk_create(new_images, batch_size=500)
        return len(new_images)
