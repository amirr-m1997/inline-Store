from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Category, CategorySlugRedirect


class FullCategoryImportTests(TestCase):
    def test_imports_the_complete_demo_tree_idempotently(self):
        call_command("import_full_category_tree")
        self.assertEqual(Category.objects.count(), 834)

    def test_tree_endpoint_returns_the_complete_imported_hierarchy(self):
        call_command("import_full_category_tree")
        response = self.client.get("/api/v1/categories/tree/")

        self.assertEqual(response.status_code, 200)
        tree = response.json()
        self.assertEqual(len(tree), 14)
        self.assertEqual(self.count_nodes(tree), 834)
        self.assertEqual(self.max_depth(tree), 2)

    def test_every_imported_category_slug_resolves(self):
        call_command("import_full_category_tree")
        categories = Category.objects.filter(is_active=True).only("id", "slug")
        self.assertEqual(categories.count(), 834)
        for category in categories:
            response = self.client.get(f"/api/v1/categories/by-slug/{category.slug}/")
            self.assertEqual(response.status_code, 200, category.slug)
            self.assertEqual(response.json()["id"], category.id)

    def test_slug_migration_preserves_categories_and_old_urls(self):
        call_command("import_full_category_tree")
        category = Category.objects.get(name_fa="پیچ های آلنی")
        category_id, parent_id, old_slug = category.id, category.parent_id, "category-1-1-1"
        Category.objects.filter(pk=category.pk).update(slug=old_slug)
        call_command("migrate_category_slugs")
        category.refresh_from_db()
        self.assertEqual(category.id, category_id)
        self.assertEqual(category.parent_id, parent_id)
        self.assertEqual(category.slug, "pich-haye-alleni")
        self.assertEqual(CategorySlugRedirect.objects.get(old_slug=old_slug).category_id, category.id)
        response = self.client.get(f"/api/v1/categories/by-slug/{old_slug}/")
        self.assertEqual(response.json()["redirect_slug"], category.slug)

    @staticmethod
    def count_nodes(nodes):
        return sum(1 + FullCategoryImportTests.count_nodes(node["children"]) for node in nodes)

    @staticmethod
    def max_depth(nodes):
        return max((FullCategoryImportTests.max_depth(node["children"]) + 1 for node in nodes), default=-1)
        self.assertEqual(Category.objects.filter(parent=None).count(), 14)
        self.assertEqual(max(Category.objects.values_list("level", flat=True)), 2)

        call_command("import_full_category_tree")
        self.assertEqual(Category.objects.count(), 834)
