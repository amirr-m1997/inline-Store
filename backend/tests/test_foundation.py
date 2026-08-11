from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.accounts.models import User
from apps.catalog.models import Category, CategorySlugRedirect, Product, SupplyBrand
from apps.catalog.slugs import latin_category_slug
from apps.carts.models import Cart, CartItem
from apps.inventory.models import Inventory

class FoundationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="tools", name_fa="ابزار", name_en="Tools", slug="tools")
        self.product = Product.objects.create(code="P-001", name="Sample", slug="sample", category=self.category, unit="piece")
    def test_custom_user_and_database(self):
        user = User.objects.create_user(username="admin", email="admin@example.test", password="safe-pass")
        self.assertTrue(user.check_password("safe-pass"))
    def test_category_hierarchy(self):
        child = Category.objects.create(code="hand", name_fa="دستی", slug="hand", parent=self.category)
        self.assertEqual(child.level, 1)
    def test_product_creation(self): self.assertEqual(self.product.code, "P-001")
    def test_inventory_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): Inventory.objects.create(product=self.product, on_hand_quantity=1, reserved_quantity=2)
    def test_cart_product_uniqueness(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): CartItem.objects.create(cart=cart, product=self.product, quantity=1)
    def test_api_root(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "v1")

    def test_paginated_product_api(self):
        response = self.client.get("/api/v1/products/?search=P-001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["available_quantity"], None)

    def test_category_filter_includes_only_its_branch(self):
        child = Category.objects.create(code="child", name_fa="زیرگروه", slug="child", parent=self.category)
        leaf = Category.objects.create(code="leaf", name_fa="برگ", slug="leaf", parent=child)
        Product.objects.create(code="P-CHILD", name="Child product", slug="child-product", category=child, unit="piece")
        leaf_product = Product.objects.create(code="P-LEAF", name="Leaf product", slug="leaf-product", category=leaf, unit="piece")
        other = Category.objects.create(code="other", name_fa="سایر", slug="other")
        Product.objects.create(code="P-OTHER", name="Other product", slug="other-product", category=other, unit="piece")
        response = self.client.get(f"/api/v1/products/?category={self.category.id}")
        self.assertEqual({item["code"] for item in response.json()["results"]}, {"P-001", "P-CHILD", "P-LEAF"})
        child_response = self.client.get(f"/api/v1/products/?category={child.id}")
        self.assertEqual({item["code"] for item in child_response.json()["results"]}, {"P-CHILD", "P-LEAF"})
        leaf_response = self.client.get(f"/api/v1/products/?category={leaf.id}")
        self.assertEqual({item["code"] for item in leaf_response.json()["results"]}, {"P-LEAF"})
        for category in (self.category, child, leaf):
            detail = self.client.get(f"/api/v1/categories/by-slug/{category.slug}/")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()["id"], category.id)
        product_detail = self.client.get(f"/api/v1/catalog/products/{leaf_product.slug}/")
        self.assertEqual([item["slug"] for item in product_detail.json()["category_tree"]], ["tools", "child", "leaf"])

    def test_category_tree_preserves_hierarchy(self):
        child = Category.objects.create(code="child", name_fa="زیرگروه", slug="child", parent=self.category)
        leaf = Category.objects.create(code="leaf", name_fa="برگ", slug="leaf", parent=child)
        response = self.client.get("/api/v1/categories/tree/")
        root = next(item for item in response.json() if item["id"] == self.category.id)
        self.assertEqual(root["children"][0]["id"], child.id)
        self.assertEqual(root["children"][0]["children"][0]["id"], leaf.id)

    def test_category_slug_is_globally_unique(self):
        with self.assertRaises(ValidationError):
            Category.objects.create(code="duplicate", name_fa="تکراری", slug=self.category.slug)

    def test_category_slug_is_generated_only_when_missing(self):
        category = Category.objects.create(code="allen", name_fa="پیچ های آلنی")
        self.assertEqual(category.slug, "pich-haye-alleni")
        category.name_fa = "نام تازه"
        category.save()
        self.assertEqual(category.slug, "pich-haye-alleni")

    def test_expected_persian_transliterations(self):
        self.assertEqual(latin_category_slug("مواد اولیه تولید"), "mavade-avalie-tolid")
        self.assertEqual(latin_category_slug("پیچ شش گوش"), "pich-shesh-goosh")
        self.assertEqual(latin_category_slug("واشر تخت"), "washer-takht")

    def test_legacy_category_slug_resolves_to_canonical_slug(self):
        CategorySlugRedirect.objects.create(old_slug="category-1", category=self.category)
        response = self.client.get("/api/v1/categories/by-slug/category-1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.category.id)
        self.assertEqual(response.json()["redirect_slug"], "tools")

    def test_in_stock_filter_is_applied_in_database(self):
        Inventory.objects.create(product=self.product, on_hand_quantity=3, reserved_quantity=3)
        response = self.client.get("/api/v1/products/?in_stock=true")
        self.assertEqual(response.json()["count"], 0)
        self.product.inventory.reserved_quantity = 1
        self.product.inventory.save()
        response = self.client.get("/api/v1/products/?in_stock=true")
        self.assertEqual(response.json()["count"], 1)

    def test_featured_filter_only_returns_admin_selected_products(self):
        selected = Product.objects.create(code="P-FEATURED", name="Featured", slug="featured", category=self.category, unit="piece", is_featured=True)
        response = self.client.get("/api/v1/products/?featured=true")
        self.assertEqual([item["id"] for item in response.json()["results"]], [selected.id])

    def test_only_active_supply_brands_are_public(self):
        SupplyBrand.objects.create(name="Active brand", is_active=True)
        SupplyBrand.objects.create(name="Hidden brand", is_active=False)
        response = self.client.get("/api/v1/supply-brands/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.json()], ["Active brand"])

    def test_missing_or_inactive_category_is_not_resolved(self):
        self.assertEqual(self.client.get("/api/v1/categories/by-slug/missing/").status_code, 404)
        self.category.is_active = False
        self.category.save()
        self.assertEqual(self.client.get("/api/v1/categories/by-slug/tools/").status_code, 404)
