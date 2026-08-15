from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductDocument


class ProductDocumentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        category = Category.objects.create(code="docs", name_fa="اسناد", slug="docs")
        self.product = Product.objects.create(code="DOC-1", name="Documented product", slug="documented-product", category=category, unit="piece")

    def make_document(self, **kwargs):
        defaults = {
            "product": self.product,
            "document_type": "datasheet",
            "title_fa": "برگه فنی",
            "file": SimpleUploadedFile("datasheet.pdf", b"pdf", content_type="application/pdf"),
            "is_published": True,
        }
        defaults.update(kwargs)
        return ProductDocument.objects.create(**defaults)

    def test_unpublished_documents_are_excluded_and_type_filter_works(self):
        self.make_document(title_fa="Hidden", is_published=False)
        manual = self.make_document(document_type="manual", title_fa="Manual", file=SimpleUploadedFile("manual.pdf", b"pdf", content_type="application/pdf"))

        response = self.client.get("/api/v1/catalog/documents/?document_type=manual")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [manual.id])

    def test_product_detail_serializes_published_documents(self):
        document = self.make_document(display_name="datasheet.pdf", revision="A", language="en")

        response = self.client.get(f"/api/v1/catalog/products/{self.product.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["documents"][0]["id"], document.id)
        self.assertEqual(response.json()["documents"][0]["file_name"], "datasheet.pdf")

    def test_file_validation_rejects_oversize_and_wrong_extension(self):
        oversized = ProductDocument(product=self.product, document_type="datasheet", file=SimpleUploadedFile("large.pdf", b"x" * (25 * 1024 * 1024 + 1), content_type="application/pdf"))
        with self.assertRaises(ValidationError):
            oversized.full_clean()
        wrong_type = ProductDocument(product=self.product, document_type="datasheet", file=SimpleUploadedFile("drawing.dwg", b"dwg", content_type="application/octet-stream"))
        with self.assertRaises(ValidationError):
            wrong_type.full_clean()
