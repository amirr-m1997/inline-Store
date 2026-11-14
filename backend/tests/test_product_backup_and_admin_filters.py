from datetime import timedelta
import io
import openpyxl
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.export_services import (
    build_products_excel_workbook,
    chunk_text_safely,
    clean_html_description,
    estimate_pages_and_stats,
    export_products_to_excel_response,
)
from apps.catalog.models import Category, Product, ProductBrand
from apps.inventory.models import Inventory

User = get_user_model()


class ProductBackupAndFiltersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            phone="09123456789",
            password="test-password-123",
            is_staff=True,
            is_superuser=True,
        )
        self.client = Client()
        self.client.force_login(self.user)

        self.category = Category.objects.create(code="CAT01", name_fa="چیلرها و سردخانه‌ها")
        self.brand = ProductBrand.objects.create(name="مهر اصل")

        # Product 1: Standard product
        self.p1 = Product.objects.create(
            code="P1001",
            name="چیلر تراکمی ۱۰۰ تن",
            slug="chiller-100-ton",
            category=self.category,
            brand=self.brand,
            unit="دستگاه",
            description="<p>این یک توضیح تستی است.</p>",
        )
        Inventory.objects.create(product=self.p1, on_hand_quantity=5, reserved_quantity=1)

        # Product 2: Product with massive multi-page description (> 10 pages)
        multi_page_html = "".join([f"<h3>فصل {i}</h3><p>توضیحات مفصل دستگاه برای بخش شماره {i} شامل پارامترهای حرارتی و برودتی استاندارد صنعت تبرید کشور...</p>" for i in range(1, 40)])
        self.p2 = Product.objects.create(
            code="P1002",
            name="چیلر اسکرو صنعتی ویژه",
            slug="chiller-screw-industrial",
            category=self.category,
            brand=self.brand,
            unit="دستگاه",
            description=multi_page_html,
        )
        Inventory.objects.create(product=self.p2, on_hand_quantity=2, reserved_quantity=0)

    def test_clean_html_description(self):
        html_input = "<h2>عنوان</h2><p>متن پاراگراف اول</p><ul><li>مورد ۱</li><li>مورد ۲</li></ul>"
        cleaned = clean_html_description(html_input)
        self.assertIn("عنوان", cleaned)
        self.assertIn("متن پاراگراف اول", cleaned)
        self.assertIn("• مورد ۱", cleaned)
        self.assertNotIn("<h2>", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<ul>", cleaned)

    def test_estimate_pages_and_stats(self):
        short_text = "این یک متن کوتاه است."
        pages, words, chars, label = estimate_pages_and_stats(short_text)
        self.assertEqual(pages, 1)
        self.assertEqual(words, 5)

        long_text = "کلمه " * 1500  # approx 7500 chars -> multiple pages
        pages, words, chars, label = estimate_pages_and_stats(long_text)
        self.assertGreater(pages, 1)
        self.assertIn("صفحه", label)

    def test_chunk_text_safely(self):
        huge_text = "الف" * 60000
        chunks = chunk_text_safely(huge_text, max_chunk_size=20000)
        self.assertGreaterEqual(len(chunks), 3)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 20000)

    def test_build_products_excel_workbook(self):
        qs = Product.objects.all()
        wb = build_products_excel_workbook(qs)
        self.assertIn("فهرست و مشخصات محصولات", wb.sheetnames)
        self.assertIn("توضیحات طولانی و کامل", wb.sheetnames)

        ws_main = wb["فهرست و مشخصات محصولات"]
        self.assertTrue(ws_main.sheet_view.rightToLeft)
        # Row 1 is header, Rows 2 and 3 are products
        self.assertEqual(ws_main.max_row, 3)

        # Check Sheet 2 holds the long description of P1002
        ws_long = wb["توضیحات طولانی و کامل"]
        self.assertTrue(ws_long.sheet_view.rightToLeft)
        self.assertGreaterEqual(ws_long.max_row, 2)

    def test_export_products_to_excel_response(self):
        qs = Product.objects.all()
        response = export_products_to_excel_response(qs)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("attachment;", response["Content-Disposition"])
        # Verify valid excel file content
        file_bytes = io.BytesIO(response.content)
        loaded_wb = openpyxl.load_workbook(file_bytes)
        self.assertIn("فهرست و مشخصات محصولات", loaded_wb.sheetnames)

    def test_admin_export_excel_endpoint(self):
        url = reverse("admin:catalog_product_export_excel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_admin_export_excel_with_filters(self):
        url = reverse("admin:catalog_product_export_excel") + "?recently_created=7d"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_preview_description_view(self):
        url = reverse("admin:catalog_product_preview_description", args=[self.p2.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.p2.name)
        self.assertContains(response, "توضیحات مفصل دستگاه")
