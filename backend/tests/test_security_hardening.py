"""Regression tests for the security-hardening pass.

Locks in: staff-only internal endpoints, no purchase-cost leak in the public
catalog serializer, mock-payment kill switch, and the global
IsAuthenticatedOrReadOnly default (public reads stay open).
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token

from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory

User = get_user_model()


class InternalEndpointsAreStaffOnlyTests(TestCase):
    def test_anonymous_is_rejected_from_internal_endpoints(self):
        for url in (
            "/api/v1/inventory/stock/",
            "/api/v1/inventory/receipts/",
            "/api/v1/inventory/issues/",
            "/api/v1/pricing/currency-rates/",
            "/api/v1/pricing/product-prices/",
            "/api/v1/dashboard/",
        ):
            response = self.client.get(url)
            self.assertIn(response.status_code, (401, 403), url)

    def test_non_staff_user_is_rejected_from_back_office_endpoints(self):
        user = User.objects.create_user(username="plain", password="x")
        token = Token.objects.create(user=user)
        for url in (
            "/api/v1/inventory/receipts/",
            "/api/v1/pricing/currency-rates/",
            "/api/v1/dashboard/",
        ):
            self.assertEqual(self.client.get(url, HTTP_AUTHORIZATION=f"Token {token.key}").status_code, 403, url)


class PublicCatalogStaysOpenTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(code="T", name_fa="نوع", slug="t", level=0)
        self.product = Product.objects.create(code="P-1", name="کالا", slug="p-1", category=self.category, unit="عدد")
        Inventory.objects.create(product=self.product, on_hand_quantity=5, reserved_quantity=0)

    def test_anonymous_product_reads_still_work(self):
        self.assertEqual(self.client.get("/api/v1/products/").status_code, 200)
        detail = self.client.get(f"/api/v1/catalog/products/{self.product.slug}/")
        self.assertEqual(detail.status_code, 200)
        pricing = detail.json()["pricing"]
        for leaked in ("last_purchase_irr", "receipt_usd_rate", "last_purchase_usd", "today_irr_equivalent"):
            self.assertNotIn(leaked, pricing)
        self.assertIn("final_price", pricing)


class MockPaymentKillSwitchTests(TestCase):
    @override_settings(PAYMENTS_MOCK_ENABLED=False)
    def test_mock_complete_is_disabled_when_flag_off(self):
        response = self.client.post("/api/v1/orders/payments/1/mock-complete/", {"outcome": "success"}, content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_logout_stays_reachable_without_credentials(self):
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 204)
