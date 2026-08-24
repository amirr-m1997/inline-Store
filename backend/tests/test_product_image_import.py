import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.catalog.models import Category, Product, ProductImage


class ProductImageImportCommandTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.media_root = Path(self.temp_dir.name) / "media"
        self.source = self.media_root / "products"
        (self.source / "2026" / "08").mkdir(parents=True)
        self.category = Category.objects.create(code="catalog", name_fa="کاتالوگ", slug="catalog")
        self.product = Product.objects.create(
            code="1001001000078", name="Test product", slug="test-product", category=self.category, unit="piece"
        )

    @override_settings(MEDIA_ROOT="/unused")
    def test_dry_run_does_not_create_records(self):
        image_file = self.source / "2026" / "08" / "1001001000078.jpg"
        image_file.write_bytes(b"image")
        with override_settings(MEDIA_ROOT=self.media_root):
            call_command("import_product_images", "--dry-run")
        self.assertEqual(ProductImage.objects.count(), 0)

    def test_import_links_exact_code_suffix_variants_and_skips_unknown_files(self):
        image_file = self.source / "2026" / "08" / "1001001000078.jpg"
        extra_image_file = self.source / "2026" / "08" / "1001001000078_1.jpg"
        image_file.write_bytes(b"image")
        extra_image_file.write_bytes(b"image")
        (self.source / "2026" / "08" / "unknown.jpg").write_bytes(b"image")
        with override_settings(MEDIA_ROOT=self.media_root):
            call_command("import_product_images")
            call_command("import_product_images")
        images = list(ProductImage.objects.order_by("sort_order", "id"))
        self.assertEqual(len(images), 2)
        self.assertEqual([image.product for image in images], [self.product, self.product])
        self.assertEqual(
            [image.image.name for image in images],
            ["products/2026/08/1001001000078.jpg", "products/2026/08/1001001000078_1.jpg"],
        )
        self.assertEqual([image.is_primary for image in images], [True, False])
