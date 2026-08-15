from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.website.models import CustomerSupportRequest, WarrantyRegistration
from apps.catalog.models import Category, Product
from apps.orders.models import Order


class SupportPrivacyTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.a = user.objects.create_user(username="support-a", password="x", phone="09120000001")
        self.b = user.objects.create_user(username="support-b", password="x", phone="09120000002")
        self.warranty = WarrantyRegistration.objects.create(customer=self.b, full_name="B", phone="09120000002")
        self.request = CustomerSupportRequest.objects.create(customer=self.b, full_name="B", phone="09120000002", subject="private", message="private")
        self.client = APIClient()

    def test_anonymous_history_is_empty(self):
        self.assertEqual(self.client.get("/api/v1/site/support/warranty-registrations/").json(), [])
        self.assertEqual(self.client.get("/api/v1/site/support/requests/").json(), [])

    def test_user_cannot_list_other_users_records_or_spoof_owner(self):
        self.client.force_authenticate(self.a)
        self.assertEqual(self.client.get("/api/v1/site/support/warranty-registrations/").json(), [])
        self.assertEqual(self.client.get("/api/v1/site/support/requests/").json(), [])
        response = self.client.post("/api/v1/site/support/requests/", {"customer": self.b.pk, "full_name": "A", "phone": "09120000001", "subject": "x", "message": "x"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CustomerSupportRequest.objects.get(reference=response.json()["reference"]).customer, self.a)
        self.assertNotIn("customer", response.json())
        self.assertNotIn("internal_notes", response.json())

    def test_history_has_no_detail_endpoint_for_guessed_references(self):
        self.client.force_authenticate(self.a)
        self.assertEqual(self.client.get(f"/api/v1/site/support/requests/{self.request.reference}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/site/support/warranty-registrations/{self.warranty.reference}/").status_code, 404)

    def test_order_context_requires_authenticated_owner(self):
        category = Category.objects.create(code="CTX", name_fa="Context", slug="context")
        product = Product.objects.create(code="CTX-1", name="Context product", slug="context-product", category=category, unit="item")
        foreign_order = Order.objects.create(customer=self.b)
        self.client.force_authenticate(self.a)
        response = self.client.post("/api/v1/site/support/requests/", {"product": product.pk, "order": foreign_order.pk, "full_name": "A", "phone": "09120000001", "subject": "x", "message": "x"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.client.force_authenticate(None)
        response = self.client.post("/api/v1/site/support/requests/", {"product": product.pk, "order": foreign_order.pk, "full_name": "Guest", "phone": "09120000003", "subject": "x", "message": "x"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_owned_order_context_is_accepted_without_exposing_owner_fields(self):
        order = Order.objects.create(customer=self.a)
        self.client.force_authenticate(self.a)
        response = self.client.post("/api/v1/site/support/requests/", {"order": order.pk, "full_name": "A", "phone": "09120000001", "subject": "order help", "message": "x"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CustomerSupportRequest.objects.get(reference=response.json()["reference"]).order_id, order.pk)
        self.assertNotIn("customer", response.json())
