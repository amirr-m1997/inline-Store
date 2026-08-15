from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib import admin as django_admin
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.carts.models import Cart, CartItem
from apps.rfq.models import RequestForQuotation, RequestForQuotationItem, SalesQuotation, SalesQuotationItem, SalesQuotationResponse
from apps.rfq.admin import RequestForQuotationAdmin
from apps.rfq.services import generate_quotation_pdf
from apps.common.document_typography import register_document_fonts, typography_status


class RfqApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="rfq-a", password="x", email="a@example.test")
        self.other = get_user_model().objects.create_user(username="rfq-b", password="x", email="b@example.test")
        category = Category.objects.create(code="RFQ-CAT", name_fa="دسته استعلام", slug="rfq-category")
        self.product = Product.objects.create(code="RFQ-P-1", name="RFQ product", slug="rfq-product", category=category, unit="عدد", is_active=True)
        self.inactive = Product.objects.create(code="RFQ-P-2", name="Hidden RFQ product", slug="hidden-rfq-product", category=category, unit="عدد", is_active=False)
        self.client = APIClient()

    def payload(self, **overrides):
        value = {"contact_name": "Buyer", "phone": "09121234567", "company_name": "Example Co", "message": "Need a review", "items": [{"product": self.product.pk, "requested_quantity": 2}]}
        value.update(overrides)
        return value

    def test_authenticated_submission_assigns_owner_and_ignores_spoofed_fields(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/rfq/", {**self.payload(), "customer": self.other.pk, "status": "quoted", "internal_notes": "secret"}, format="json")
        self.assertEqual(response.status_code, 201)
        record = RequestForQuotation.objects.get(reference=response.json()["reference"])
        self.assertEqual(record.customer_id, self.user.pk)
        self.assertEqual(record.status, RequestForQuotation.Status.SUBMITTED)
        self.assertEqual(record.items.count(), 1)
        self.assertNotIn("internal_notes", response.json())
        self.assertNotIn("customer", response.json())

    def test_anonymous_submission_is_allowed_but_history_is_private(self):
        response = self.client.post("/api/v1/rfq/", self.payload(email="guest@example.test"), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(RequestForQuotation.objects.get(reference=response.json()["reference"]).customer_id)
        self.assertEqual(self.client.get("/api/v1/rfq/").json(), [])

    def test_history_and_detail_are_strictly_owner_scoped(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/rfq/", self.payload(), format="json")
        reference = response.json()["reference"]
        RequestForQuotation.objects.create(customer=self.other, contact_name="Other", phone="09120000001", message="Other request")
        self.assertEqual(len(self.client.get("/api/v1/rfq/").json()), 1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/rfq/{reference}/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/v1/rfq/{reference}/").status_code, 401)

    def test_product_and_quantity_validation(self):
        for item in ({"product": self.inactive.pk, "requested_quantity": 1}, {"product": self.product.pk, "requested_quantity": 0}):
            response = self.client.post("/api/v1/rfq/", self.payload(items=[item]), format="json")
            self.assertEqual(response.status_code, 400)

    def test_variant_is_not_invented_and_duplicate_products_are_rejected(self):
        duplicate = [{"product": self.product.pk, "requested_quantity": 1}, {"product": self.product.pk, "requested_quantity": 2}]
        response = self.client.post("/api/v1/rfq/", self.payload(items=duplicate), format="json")
        self.assertEqual(response.status_code, 400)

    def test_invalid_item_does_not_create_partial_rfq(self):
        response = self.client.post("/api/v1/rfq/", self.payload(items=[{"product": self.product.pk, "requested_quantity": 1}, {"product": self.inactive.pk, "requested_quantity": 1}]), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RequestForQuotation.objects.count(), 0)
        self.assertEqual(RequestForQuotationItem.objects.count(), 0)

    def test_bounded_items_and_meaningful_request_validation(self):
        self.assertEqual(self.client.post("/api/v1/rfq/", self.payload(message="", items=[]), format="json").status_code, 400)
        too_many = [{"product": self.product.pk, "requested_quantity": 1} for _ in range(26)]
        self.assertEqual(self.client.post("/api/v1/rfq/", self.payload(items=too_many), format="json").status_code, 400)

    def test_multi_item_submission_uses_one_reference_and_preserves_item_context(self):
        second = Product.objects.create(code="RFQ-P-3", name="Second RFQ product", slug="second-rfq-product", category=self.product.category, unit="عدد", is_active=True)
        response = self.client.post("/api/v1/rfq/", self.payload(items=[
            {"product": self.product.pk, "requested_quantity": 2, "customer_note": "First note"},
            {"product": second.pk, "requested_quantity": 4, "customer_note": "Second note"},
        ]), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()["items"]), 2)
        self.assertEqual(RequestForQuotation.objects.count(), 1)
        self.assertEqual(RequestForQuotationItem.objects.filter(rfq__reference=response.json()["reference"]).count(), 2)

    def test_cart_context_is_trusted_eligible_and_does_not_mutate_cart(self):
        cart = Cart.objects.create()
        inactive_item = CartItem.objects.create(cart=cart, product=self.inactive, quantity=3)
        active_item = CartItem.objects.create(cart=cart, product=self.product, quantity=4)
        before = list(CartItem.objects.filter(cart=cart).values_list("product_id", "quantity"))
        response = self.client.get("/api/v1/rfq/cart-context/", HTTP_X_GUEST_TOKEN=str(cart.guest_token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["id"], self.product.pk)
        self.assertEqual(response.json()["items"][0]["quantity"], 4)
        self.assertEqual(response.json()["omitted_count"], 1)
        self.assertEqual(list(CartItem.objects.filter(cart=cart).values_list("product_id", "quantity")), before)
        self.assertEqual(inactive_item.quantity, 3)
        self.assertEqual(active_item.quantity, 4)


class RfqAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username="rfq-admin", email="rfq-admin@example.test", password="x")
        self.client = APIClient()
        self.client.login(username="rfq-admin", password="x")

    def test_changelist_and_change_page_render(self):
        record = RequestForQuotation.objects.create(contact_name="Anonymous", phone="09120000001", message="Admin test")
        self.assertEqual(self.client.get("/admin/rfq/requestforquotation/").status_code, 200)
        self.assertEqual(self.client.get(f"/admin/rfq/requestforquotation/{record.pk}/change/").status_code, 200)
        quote = SalesQuotation.objects.create(rfq=record)
        self.assertEqual(self.client.get("/admin/rfq/salesquotation/").status_code, 200)
        self.assertEqual(self.client.get(f"/admin/rfq/salesquotation/{quote.pk}/change/").status_code, 200)

    def test_multi_item_rfq_draft_initialization_copies_all_items_without_prices(self):
        category = Category.objects.create(code="ADMIN-RFQ-CAT", name_fa="دسته", slug="admin-rfq-category")
        first = Product.objects.create(code="ADMIN-RFQ-1", name="Admin product one", slug="admin-rfq-one", category=category, unit="عدد", is_active=True)
        second = Product.objects.create(code="ADMIN-RFQ-2", name="Admin product two", slug="admin-rfq-two", category=category, unit="عدد", is_active=True)
        record = RequestForQuotation.objects.create(contact_name="Buyer", phone="09120000001", message="Multiple")
        for product, quantity in ((first, 2), (second, 5)):
            RequestForQuotationItem.objects.create(rfq=record, product=product, requested_quantity=quantity, product_code_snapshot=product.code, product_name_snapshot=product.name)
        model_admin = RequestForQuotationAdmin(RequestForQuotation, django_admin.site)
        model_admin.message_user = lambda *args, **kwargs: None
        model_admin.create_quotation_draft(type("Request", (), {"user": self.admin})(), RequestForQuotation.objects.filter(pk=record.pk))
        quotation = SalesQuotation.objects.get(rfq=record)
        self.assertEqual(quotation.items.count(), 2)
        self.assertEqual(set(quotation.items.values_list("quantity", flat=True)), {2, 5})
        self.assertTrue(all(item.unit_price == 0 for item in quotation.items.all()))


class QuotationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="quote-a", password="x")
        self.other = get_user_model().objects.create_user(username="quote-b", password="x")
        category = Category.objects.create(code="QUOTE-CAT", name_fa="دسته پیشنهاد", slug="quote-category")
        self.product = Product.objects.create(code="QUOTE-P-1", name="Quoted product", slug="quoted-product", category=category, unit="عدد", is_active=True)
        self.rfq = RequestForQuotation.objects.create(customer=self.user, contact_name="Buyer", phone="09121234567", message="Need quote")
        self.rfq_item = RequestForQuotationItem.objects.create(rfq=self.rfq, product=self.product, requested_quantity=2, product_code_snapshot=self.product.code, product_name_snapshot=self.product.name)
        self.client = APIClient()

    def make_issued(self):
        quote = SalesQuotation.objects.create(rfq=self.rfq, status=SalesQuotation.Status.DRAFT, currency=SalesQuotation.Currency.IRR)
        item = SalesQuotationItem.objects.create(quotation=quote, source_rfq_item=self.rfq_item, product=self.product, product_name_snapshot=self.product.name, product_code_snapshot=self.product.code, quantity=2, unit_price="125.50")
        quote.status = SalesQuotation.Status.ISSUED
        quote.issued_at = timezone.now()
        quote.full_clean()
        quote.save()
        return quote, item

    def test_issued_customer_visibility_and_decimal_total(self):
        quote, item = self.make_issued()
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subtotal"], "251.00")
        self.assertNotIn("internal_notes", response.json())
        self.assertNotIn("created_by", response.json())
        with self.assertRaises(Exception):
            item.unit_price = "130.00"
            item.save()

    def test_owned_issued_pdf_is_private_and_contains_no_internal_note(self):
        quote, _ = self.make_issued()
        quote.internal_notes = "SECRET MARGIN ANALYSIS"
        quote.save(update_fields=("internal_notes",))
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/pdf/?locale=en")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(f"quotation-{quote.reference}.pdf", response["Content-Disposition"])
        content = b"".join(response.streaming_content)
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertNotIn(b"SECRET MARGIN ANALYSIS", content)
        self.assertGreater(len(content), 1000)

    def test_pdf_draft_and_cross_user_access_are_blocked(self):
        draft = SalesQuotation.objects.create(rfq=self.rfq)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{draft.reference}/pdf/").status_code, 404)
        other_rfq = RequestForQuotation.objects.create(customer=self.user, contact_name="Buyer two", phone="09121234567", message="Need another quote")
        other_item = RequestForQuotationItem.objects.create(rfq=other_rfq, product=self.product, requested_quantity=1, product_code_snapshot=self.product.code, product_name_snapshot=self.product.name)
        self.rfq, self.rfq_item = other_rfq, other_item
        quote, _ = self.make_issued()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/pdf/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/pdf/").status_code, 401)

    def test_pdf_generation_supports_long_multi_page_quotation(self):
        quote, item = self.make_issued()
        SalesQuotationItem.objects.filter(pk=item.pk).update(product_name_snapshot="محصول فنی نمونه با نام طولانی برای آزمون صفحه‌بندی " * 4)
        SalesQuotationItem.objects.bulk_create([
            SalesQuotationItem(quotation=quote, product=self.product, product_name_snapshot=f"محصول آزمون {index} " * 8, product_code_snapshot=f"LONG-{index}", quantity=1, unit_price="10.00")
            for index in range(2, 35)
        ])
        content = generate_quotation_pdf(SalesQuotation.objects.prefetch_related("items").get(pk=quote.pk), locale="fa")
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertGreater(len(content), 4000)

    def test_drafts_anonymous_and_other_users_are_private(self):
        draft = SalesQuotation.objects.create(rfq=self.rfq)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{draft.reference}/").status_code, 404)
        other_rfq = RequestForQuotation.objects.create(customer=self.user, contact_name="Buyer two", phone="09121234567", message="Need another quote")
        other_item = RequestForQuotationItem.objects.create(rfq=other_rfq, product=self.product, requested_quantity=1, product_code_snapshot=self.product.code, product_name_snapshot=self.product.name)
        self.rfq, self.rfq_item = other_rfq, other_item
        quote, _ = self.make_issued()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/").status_code, 401)

    def test_issued_requires_currency_items_and_prices(self):
        quote = SalesQuotation.objects.create(rfq=self.rfq, status=SalesQuotation.Status.ISSUED)
        with self.assertRaises(Exception):
            quote.full_clean()

    def test_owner_can_accept_and_issued_values_and_pdf_remain_unchanged(self):
        quote, item = self.make_issued()
        original_pdf = generate_quotation_pdf(SalesQuotation.objects.prefetch_related("items").get(pk=quote.pk), locale="fa")
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "accepted"}, format="json")
        self.assertEqual(response.status_code, 201)
        saved = SalesQuotationResponse.objects.get(quotation=quote)
        self.assertEqual(saved.customer_id, self.user.pk)
        self.assertIsNotNone(saved.response_at)
        self.assertEqual(self.client.get(f"/api/v1/rfq/quotations/{quote.reference}/").json()["customer_response"]["response"], "accepted")
        item.refresh_from_db(); quote.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal("125.50"))
        self.assertEqual(quote.status, SalesQuotation.Status.ISSUED)
        regenerated_pdf = generate_quotation_pdf(SalesQuotation.objects.prefetch_related("items").get(pk=quote.pk), locale="fa")
        self.assertTrue(original_pdf.startswith(b"%PDF"))
        self.assertTrue(regenerated_pdf.startswith(b"%PDF"))
        self.assertGreater(len(regenerated_pdf), 1000)

    def test_owner_can_reject_or_request_revision_and_revision_reopens_rfq(self):
        quote, _ = self.make_issued()
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "revision_requested", "note": "لطفاً مقدار قلم را بررسی کنید."}, format="json")
        self.assertEqual(response.status_code, 201)
        self.rfq.refresh_from_db()
        self.assertEqual(self.rfq.status, RequestForQuotation.Status.UNDER_REVIEW)
        self.assertEqual(SalesQuotationResponse.objects.get(quotation=quote).note, "لطفاً مقدار قلم را بررسی کنید.")

    def test_response_eligibility_privacy_expiry_and_duplicate_rules(self):
        quote, _ = self.make_issued()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "accepted"}, format="json").status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "accepted"}, format="json").status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "revision_requested"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "accepted"}, format="json").status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "rejected"}, format="json").status_code, 400)
        draft = SalesQuotation.objects.create(rfq=RequestForQuotation.objects.create(customer=self.user, contact_name="Draft", phone="09121234567", message="Draft"))
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{draft.reference}/respond/", {"response": "accepted"}, format="json").status_code, 400)

    def test_expired_quotation_cannot_receive_response(self):
        quote, _ = self.make_issued()
        quote.expires_at = timezone.now() - timedelta(days=1)
        quote.save(update_fields=("expires_at", "updated_at"))
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f"/api/v1/rfq/quotations/{quote.reference}/respond/", {"response": "accepted"}, format="json").status_code, 400)

    def test_shared_document_typography_policy_reports_vazir_asset_state(self):
        status = typography_status()
        self.assertIn("vazir_available", status)
        self.assertEqual(set(status["weights"]), {"regular", "medium", "bold"})
        self.assertTrue(status["vazir_available"])
        self.assertTrue(all(path and path.is_file() for path in status["weights"].values()))

    def test_shared_document_typography_registers_real_vazir_weights(self):
        from reportlab.pdfbase import pdfmetrics

        fonts = register_document_fonts()
        self.assertEqual(fonts["status"]["vazir_available"], True)
        self.assertIn(fonts["persian"], pdfmetrics.getRegisteredFontNames())
        self.assertIn(fonts["persian_medium"], pdfmetrics.getRegisteredFontNames())
        self.assertIn(fonts["persian_bold"], pdfmetrics.getRegisteredFontNames())

    def test_english_quotation_uses_latin_document_typography(self):
        quote, _ = self.make_issued()
        content = generate_quotation_pdf(quote, locale="en")
        self.assertIn(b"DejaVuSans", content)
        self.assertNotIn(b"Vazir-Regular", content)


@override_settings(DEBUG=True)
class RfqDemoLifecycleTests(TestCase):
    def test_demo_rfq_is_idempotent_and_cleanup_preserves_manual(self):
        call_command("populate_demo_content", stdout=StringIO())
        first = RequestForQuotation.objects.filter(source="demo-content:phase-12.1").count()
        call_command("populate_demo_content", stdout=StringIO())
        self.assertEqual(first, RequestForQuotation.objects.filter(source="demo-content:phase-12.1").count())
        manual = RequestForQuotation.objects.create(contact_name="Manual", phone="09120000002", message="Manual request")
        call_command("remove_demo_content", stdout=StringIO())
        self.assertFalse(RequestForQuotation.objects.filter(source="demo-content:phase-12.1").exists())
        self.assertTrue(RequestForQuotation.objects.filter(pk=manual.pk).exists())
