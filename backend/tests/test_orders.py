from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Category, Product
from apps.inventory.models import Reservation
from apps.orders.models import Invoice, InvoiceEmailLog, Order, OrderItem, Payment, ProformaRequest


class OrderModelTests(TestCase):
    def setUp(self):
        category = Category.objects.create(code="order", name_fa="سفارش", slug="order-test")
        self.product = Product.objects.create(code="ORDER-001", name="محصول سفارش", slug="order-product", category=category, unit="عدد")
        self.order = Order.objects.create(status=Order.Status.PENDING_PAYMENT, subtotal=Decimal("200000"), discount_percentage=10, discount_amount=Decimal("20000"), final_amount=Decimal("180000"))
        self.item = OrderItem.objects.create(order=self.order, product=self.product, product_name=self.product.name, product_code=self.product.code, unit=self.product.unit, unit_price=Decimal("100000"), quantity=2, discount_percentage=10, discount_amount=Decimal("20000"), line_subtotal=Decimal("200000"), line_total=Decimal("180000"))

    def test_order_item_keeps_purchase_snapshot(self):
        self.product.name = "نام تغییرکرده"
        self.product.code = "CHANGED"
        self.product.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.product_name, "محصول سفارش")
        self.assertEqual(self.item.product_code, "ORDER-001")
        self.assertEqual(self.item.unit_price, Decimal("100000"))

    def test_all_required_order_statuses_exist(self):
        self.assertEqual(set(Order.Status.values), {"pending_payment", "processing", "confirmed", "preparing", "shipped", "delivered", "cancelled", "returned"})

    def test_payment_is_ready_for_gateway_identifiers(self):
        payment = Payment.objects.create(order=self.order, gateway="zarinpal", amount=self.order.final_amount, authority="A0001", reference_id="R0001", status=Payment.Status.VERIFIED)
        self.assertEqual(payment.authority, "A0001")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(order=self.order, gateway="zarinpal", amount=1, authority="A0001")

    def test_reservation_can_reference_order_item_during_transition(self):
        reservation = Reservation.objects.create(product=self.product, order_item=self.item, quantity=2)
        self.assertEqual(reservation.order_item_id, self.item.id)
        self.assertIsNone(reservation.cart_item_id)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MEDIA_ROOT="/tmp/company-store-test-media")
class CustomerOrderApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", phone="09121110000", password="secret123", email="buyer@example.com")
        self.other = User.objects.create_user(username="other", phone="09121110001", password="secret123")
        self.order = Order.objects.create(customer=self.user, customer_first_name="خریدار", customer_email=self.user.email,
                                          subtotal=1000, final_amount=1000)
        OrderItem.objects.create(order=self.order, product_name="محصول ثابت", product_code="P-1", unit="عدد",
                                 unit_price=1000, quantity=1, line_subtotal=1000, line_total=1000)
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_customer_can_only_read_own_orders(self):
        response = self.client.get("/api/customer/orders/")
        self.assertEqual(response.status_code, 200); self.assertEqual(response.json()[0]["id"], self.order.id)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/customer/orders/{self.order.id}/").status_code, 404)

    def test_invoice_is_snapshot_pdf_and_can_be_emailed(self):
        response = self.client.get(f"/api/customer/orders/{self.order.id}/invoice/")
        self.assertEqual(response.status_code, 200); self.assertEqual(response["Content-Type"], "application/pdf")
        invoice = Invoice.objects.get(order=self.order)
        self.assertEqual(invoice.items_snapshot[0]["product_name"], "محصول ثابت")
        response = self.client.post(f"/api/customer/orders/{self.order.id}/invoice/send/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(InvoiceEmailLog.objects.filter(invoice=invoice, recipient=self.user.email, success=True).exists())

    def test_invoice_preview_renders_rich_html(self):
        response = self.client.get(f"/api/customer/orders/{self.order.id}/invoice/?preview=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        content = response.content.decode("utf-8")
        self.assertIn(f"INV-{self.order.order_number}", content)
        self.assertIn("محصول ثابت", content)
        self.assertIn("مبلغ کل قابل پرداخت", content)

    def test_status_change_creates_history_and_timestamps(self):
        self.order.status = Order.Status.SHIPPED; self.order.save(update_fields=("status", "updated_at"))
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.shipped_at)
        self.assertEqual(self.order.status_history.last().status, Order.Status.SHIPPED)

    def test_customer_can_request_proforma_only_once(self):
        url = f"/api/customer/orders/{self.order.id}/proforma/request/"
        response = self.client.post(url, {"note": "به نام شرکت صادر شود."}, format="json")
        self.assertEqual(response.status_code, 201)
        request = ProformaRequest.objects.get(order=self.order)
        self.assertEqual(request.customer, self.user)
        self.assertEqual(request.customer_note, "به نام شرکت صادر شود.")
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 409)

    def test_customer_cannot_request_another_users_proforma(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(f"/api/customer/orders/{self.order.id}/proforma/request/", {}, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProformaRequest.objects.filter(order=self.order).exists())


class InvoiceTextTests(TestCase):
    def test_fa_digits(self):
        from apps.orders.invoice_text import fa_digits
        self.assertEqual(fa_digits(57930000), "۵۷٬۹۳۰٬۰۰۰")

    def test_amount_in_words(self):
        from apps.orders.invoice_text import amount_in_words
        self.assertEqual(amount_in_words(0), "صفر")
        self.assertEqual(amount_in_words(900000), "نهصد هزار")
        self.assertEqual(amount_in_words(57930000), "پنجاه و هفت میلیون و نهصد و سی هزار")

    def test_gregorian_to_jalali(self):
        from datetime import datetime
        from apps.orders.invoice_text import fa_date, gregorian_to_jalali
        self.assertEqual(gregorian_to_jalali(2026, 9, 18), (1405, 6, 27))
        self.assertEqual(fa_date(datetime(2026, 9, 18, 10, 42, 15)), "۱۴۰۵/۰۶/۲۷")
