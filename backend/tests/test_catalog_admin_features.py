from datetime import timedelta
from django.test import TestCase, RequestFactory
from django.utils import timezone
from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductBrand
from apps.catalog.export_services import (
    clean_html_description,
    estimate_pages_and_stats,
    build_products_excel_workbook,
    export_products_to_excel_response,
)
from apps.catalog.admin import ProductAdmin, RecentlyCreatedListFilter, RecentlyUpdatedListFilter
from django.contrib.admin.sites import AdminSite


class CatalogAdminAndExportTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.category = Category.objects.create(code="CAT1", name_fa="دسته‌بندی تست", slug="test-cat")
        self.brand = ProductBrand.objects.create(name="مهر اصل", slug="mehr-asl")
        
        # Product 1: Short description
        self.p1 = Product.objects.create(
            code="PRD-001",
            name="محصول تست ۱",
            slug="product-test-1",
            category=self.category,
            brand=self.brand,
            unit="دستگاه",
            description="<p>این یک توضیح تستی کوتاه است.</p>",
        )

        # Product 2: Long multi-page description (simulating several pages)
        long_html = "".join([f"<p>پاراگراف {i}: این بخش از متن طولانی مستندات فنی و راهنمای نصب و راه‌اندازی محصول است.</p>" for i in range(1, 150)])
        self.p2 = Product.objects.create(
            code="PRD-002",
            name="محصول تست ۲ با توضیحات چند صفحه‌ای",
            slug="product-test-2-long",
            category=self.category,
            brand=self.brand,
            unit="دستگاه",
            description=long_html,
        )

    def test_get_absolute_url(self):
        url = self.p1.get_absolute_url()
        self.assertIn("/fa/product/product-test-1", url)

    def test_clean_html_and_pages_estimation(self):
        cleaned = clean_html_description(self.p1.description)
        self.assertEqual(cleaned, "این یک توضیح تستی کوتاه است.")

        cleaned_long = clean_html_description(self.p2.description)
        pages, words, chars, label = estimate_pages_and_stats(cleaned_long)
        self.assertGreater(pages, 1)
        self.assertIn("صفحه", label)

    def test_excel_workbook_export(self):
        qs = Product.objects.filter(pk__in=[self.p1.pk, self.p2.pk])
        wb = build_products_excel_workbook(qs)
        self.assertIn("فهرست و مشخصات محصولات", wb.sheetnames)
        self.assertIn("توضیحات طولانی و کامل", wb.sheetnames)
        
        ws_main = wb["فهرست و مشخصات محصولات"]
        self.assertTrue(ws_main.sheet_view.rightToLeft)
        # Check rows exist
        self.assertEqual(ws_main.max_row, 3)  # header + 2 products

        # Test response export
        response = export_products_to_excel_response(qs)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_admin_product_name_link_and_display(self):
        model_admin = ProductAdmin(Product, self.site)
        link_html = model_admin.product_name_link(self.p1)
        self.assertIn(self.p1.get_absolute_url(), link_html)
        self.assertIn(self.p1.name, link_html)
        self.assertIn("target=\"_blank\"", link_html)
        self.assertEqual(model_admin.list_display_links, ("code",))
