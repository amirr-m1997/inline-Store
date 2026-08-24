from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.catalog.admin import CategoryAdmin, ProductAdmin
from apps.catalog.admin_widgets import CategoryPickerWidget
from apps.catalog.models import Category, Product


class CategoryAdminTreeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.root = Category.objects.create(code="root", name_fa="دسته اصلی", slug="root")
        self.child = Category.objects.create(code="child", name_fa="زیر دسته", slug="child", parent=self.root)
        self.grandchild = Category.objects.create(code="leaf", name_fa="دسته نهایی", slug="leaf", parent=self.child)

    def test_category_menu_opens_only_root_categories(self):
        self.client.force_login(self.user)
        response = self.client.get("/admin/catalog/category/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "دسته‌بندی‌های اصلی")
        self.assertContains(response, self.root.name_fa)
        self.assertNotContains(response, self.child.name_fa)
        self.assertNotContains(response, self.grandchild.name_fa)

    def test_clicking_a_category_opens_only_its_next_level(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/admin/catalog/category/browse/?parent={self.root.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.child.name_fa)
        self.assertNotContains(response, self.grandchild.name_fa)
        self.assertContains(response, "بازگشت به دسته‌های اصلی")

    def test_picker_endpoint_browses_roots_and_children(self):
        self.client.force_login(self.user)
        root_response = self.client.get("/admin/catalog/category/picker/")
        self.assertEqual(root_response.status_code, 200)
        self.assertEqual([item["id"] for item in root_response.json()["results"]], [self.root.id])
        child_response = self.client.get(f"/admin/catalog/category/picker/?parent={self.root.pk}")
        self.assertEqual([item["id"] for item in child_response.json()["results"]], [self.child.id])

    def test_product_and_parent_fields_use_category_picker(self):
        request = RequestFactory().get("/admin/catalog/product/add/")
        request.user = self.user
        product_form = ProductAdmin(Product, admin.site).get_form(request)()
        self.assertIsInstance(product_form.fields["category"].widget, CategoryPickerWidget)
        self.assertIn("category_picker.js", str(product_form.media))
        self.assertIn("category_picker.css", str(product_form.media))

        category_form = CategoryAdmin(Category, admin.site).get_form(request, obj=self.root)()
        parent_widget = category_form.fields["parent"].widget
        self.assertIsInstance(parent_widget, CategoryPickerWidget)
        self.assertIn(str(self.root.pk), parent_widget.render("parent", None))
        self.assertIn(str(self.child.pk), parent_widget.render("parent", None))