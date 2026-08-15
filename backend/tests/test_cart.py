from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.authtoken.models import Token

from apps.accounts.models import CustomerAddress, User
from apps.carts.models import Cart, DiscountCode
from apps.catalog.models import Category, Product
from apps.inventory.models import Inventory
from apps.inventory.models import Reservation
from apps.pricing.models import Currency, ProductPrice


class CartApiTests(TestCase):
    def setUp(self):
        category = Category.objects.create(code="cart", name_fa="سبد", slug="cart-test")
        self.product = Product.objects.create(code="C-001", name="کالای تست", slug="cart-product", category=category, unit="عدد")
        Inventory.objects.create(product=self.product, on_hand_quantity=10, reserved_quantity=1)

    def test_guest_cart_keeps_items_and_customer_information(self):
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 2}, content_type="application/json")
        self.assertEqual(added.status_code, 201)
        token = added.json()["guest_token"]
        customer = {
            "customer_first_name": "امیر", "customer_last_name": "محمدی", "customer_phone": "09123456789",
            "customer_email": "amir@example.test", "shipping_province": "تهران", "shipping_city": "تهران",
            "shipping_postal_code": "1234567890", "shipping_address": "نشانی کامل تست",
        }
        saved = self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(saved.json()["customer_complete"])
        self.assertEqual(saved.json()["items"][0]["quantity"], 2)

    def test_authenticated_customer_save_keeps_cart_contact_when_phone_is_not_profile_mobile(self):
        user = User.objects.create_user(username="international-buyer", email="international@example.test", password="safe-pass")
        token = Token.objects.create(user=user)
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}")
        customer = {
            "customer_first_name": "Test", "customer_last_name": "Buyer", "customer_phone": "+442071234567",
            "customer_email": "international@example.test", "shipping_province": "London", "shipping_city": "London",
            "shipping_postal_code": "1234567890", "shipping_address": "Business address",
        }
        response = self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_GUEST_TOKEN=added.json()["guest_token"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["customer"]["customer_phone"], customer["customer_phone"])
        user.refresh_from_db()
        self.assertEqual(user.phone, None)

    def test_authenticated_customer_save_rejects_duplicate_profile_email_as_client_error(self):
        existing = User.objects.create_user(username="existing-buyer", email="taken@example.test", password="safe-pass")
        user = User.objects.create_user(username="another-buyer", email="another@example.test", password="safe-pass")
        token = Token.objects.create(user=user)
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.patch("/api/v1/cart/", {"customer": {"customer_email": existing.email}}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_GUEST_TOKEN=added.json()["guest_token"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("ایمیل", response.json()["customer_email"][0])

    def test_authenticated_customer_save_rejects_duplicate_profile_phone_as_client_error(self):
        existing = User.objects.create_user(username="phone-owner", email="phone-owner@example.test", phone="09121234567", password="safe-pass")
        user = User.objects.create_user(username="phone-buyer", email="phone-buyer@example.test", password="safe-pass")
        token = Token.objects.create(user=user)
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.patch("/api/v1/cart/", {"customer": {"customer_phone": "09121234567"}}, content_type="application/json", HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_GUEST_TOKEN=added.json()["guest_token"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("شماره تماس", response.json()["customer_phone"][0])

    def test_guest_cart_merges_into_authenticated_cart(self):
        guest = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 2}, content_type="application/json")
        guest_token = guest.json()["guest_token"]
        user = User.objects.create_user(username="buyer", email="buyer@example.test", password="safe-pass")
        token = Token.objects.create(user=user)
        merged = self.client.get("/api/v1/cart/", HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_GUEST_TOKEN=guest_token)
        self.assertEqual(merged.status_code, 200)
        self.assertEqual(merged.json()["items"][0]["quantity"], 2)
        self.assertFalse(Cart.objects.filter(guest_token=guest_token, user__isnull=True).exists())

    def test_cart_rejects_quantity_above_inventory(self):
        response = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 10}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_checkout_saves_cart_and_reserves_inventory(self):
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 2}, content_type="application/json")
        token = added.json()["guest_token"]
        customer = {"customer_first_name": "امیر", "customer_last_name": "محمدی", "customer_phone": "09123456789", "shipping_province": "تهران", "shipping_city": "تهران", "shipping_postal_code": "1234567890", "shipping_address": "نشانی کامل تست"}
        self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)

        response = self.client.post("/api/v1/cart/checkout/", {}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["order_reference"].startswith("MEHR-"))
        cart = Cart.objects.get(guest_token=token)
        self.assertEqual(cart.status, Cart.Status.CHECKED_OUT)
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.reserved_quantity, 3)
        self.assertEqual(Reservation.objects.get(cart_item__cart=cart).quantity, 2)

    def test_checkout_requires_complete_customer_information(self):
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json")
        response = self.client.post("/api/v1/cart/checkout/", {}, content_type="application/json", HTTP_X_GUEST_TOKEN=added.json()["guest_token"])
        self.assertEqual(response.status_code, 400)

    def test_authenticated_order_is_listed_and_address_is_saved(self):
        user = User.objects.create_user(username="account-buyer", phone="09121234567", password="safe-pass")
        token = Token.objects.create(user=user)
        headers = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
        self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json", **headers)
        customer = {"customer_first_name": "امیر", "customer_last_name": "محمدی", "customer_phone": "09121234567", "shipping_province": "تهران", "shipping_city": "تهران", "shipping_postal_code": "1234567890", "shipping_address": "نشانی کامل تست"}
        self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", **headers)
        self.assertTrue(CustomerAddress.objects.filter(user=user, is_default=True, address="نشانی کامل تست").exists())
        checked_out = self.client.post("/api/v1/cart/checkout/", {}, content_type="application/json", **headers)
        orders = self.client.get("/api/v1/cart/orders/", **headers)
        self.assertEqual(orders.status_code, 200)
        self.assertEqual(orders.json()[0]["reference"], checked_out.json()["order_reference"])
        self.assertEqual(orders.json()[0]["items"][0]["product_name"], self.product.name)

    def test_discount_code_is_calculated_server_side_and_counted_on_checkout(self):
        ProductPrice.objects.create(product=self.product, amount=100000, currency=Currency.IRR, effective_from=timezone.now() - timedelta(days=1))
        coupon = DiscountCode.objects.create(code=" summer20 ", percentage=20, minimum_order_amount=100000, valid_from=timezone.now() - timedelta(hours=1), valid_until=timezone.now() + timedelta(days=1), max_uses=1)
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 2}, content_type="application/json")
        token = added.json()["guest_token"]
        applied = self.client.post("/api/v1/cart/discount/", {"code": "SUMMER20"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(applied.status_code, 200)
        self.assertEqual(applied.json()["subtotal"], "200000.00")
        self.assertEqual(applied.json()["discount_amount"], "40000.00")
        self.assertEqual(applied.json()["total"], "160000.00")
        customer = {"customer_first_name": "امیر", "customer_last_name": "محمدی", "customer_phone": "09123456789", "shipping_province": "تهران", "shipping_city": "تهران", "shipping_postal_code": "1234567890", "shipping_address": "نشانی کامل تست"}
        self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        checkout = self.client.post("/api/v1/cart/checkout/", {}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(checkout.status_code, 200)
        coupon.refresh_from_db(); self.assertEqual(coupon.usage_count, 0)
        paid = self.client.post(f"/api/v1/orders/payments/{checkout.json()['payment_id']}/mock-complete/", {"outcome": "success"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(paid.status_code, 200)
        coupon.refresh_from_db(); self.assertEqual(coupon.usage_count, 1)
        cart = Cart.objects.get(guest_token=token)
        self.assertEqual(str(cart.discount_amount), "40000.00")
        self.assertEqual(str(cart.final_total), "160000.00")

    def test_checkout_creates_pending_order_and_mock_payment_settles_inventory(self):
        ProductPrice.objects.create(product=self.product, amount=250000, currency=Currency.IRR, effective_from=timezone.now() - timedelta(days=1))
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 2}, content_type="application/json")
        token = added.json()["guest_token"]
        customer = {"customer_first_name": "امیر", "customer_last_name": "محمدی", "customer_phone": "09123456789", "shipping_province": "تهران", "shipping_city": "تهران", "shipping_postal_code": "1234567890", "shipping_address": "نشانی کامل تست"}
        self.client.patch("/api/v1/cart/", {"customer": customer}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        checkout = self.client.post("/api/v1/cart/checkout/", {}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(checkout.status_code, 200)
        self.assertEqual(checkout.json()["payment_url"], f"/fa/payment/{checkout.json()['payment_id']}")
        from apps.orders.models import Order, Payment
        order = Order.objects.get(pk=checkout.json()["order_id"])
        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(order.items.get().product_name, self.product.name)
        self.product.inventory.refresh_from_db(); self.assertEqual(self.product.inventory.reserved_quantity, 3)
        result = self.client.post(f"/api/v1/orders/payments/{checkout.json()['payment_id']}/mock-complete/", {"outcome": "success"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token)
        self.assertEqual(result.status_code, 200)
        order.refresh_from_db(); self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(Payment.objects.get(pk=checkout.json()["payment_id"]).status, Payment.Status.VERIFIED)
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.on_hand_quantity, 8)
        self.assertEqual(self.product.inventory.reserved_quantity, 1)
        self.assertEqual(Reservation.objects.get(order_item__order=order).status, Reservation.Status.CONVERTED)

    def test_invalid_expired_and_minimum_amount_codes_are_rejected(self):
        added = self.client.post("/api/v1/cart/items/", {"product_id": self.product.id, "quantity": 1}, content_type="application/json")
        token = added.json()["guest_token"]
        self.assertEqual(self.client.post("/api/v1/cart/discount/", {"code": "UNKNOWN"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token).status_code, 400)
        DiscountCode.objects.create(code="EXPIRED", percentage=10, valid_from=timezone.now() - timedelta(days=2), valid_until=timezone.now() - timedelta(days=1))
        self.assertEqual(self.client.post("/api/v1/cart/discount/", {"code": "EXPIRED"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token).status_code, 400)
        DiscountCode.objects.create(code="MINIMUM", percentage=10, minimum_order_amount=999999, valid_from=timezone.now() - timedelta(hours=1))
        self.assertEqual(self.client.post("/api/v1/cart/discount/", {"code": "MINIMUM"}, content_type="application/json", HTTP_X_GUEST_TOKEN=token).status_code, 400)
