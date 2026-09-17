from decimal import Decimal

from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductFavorite, ProductReview
from apps.orders.models import Order, OrderItem


class ProductSocialApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer-social", password="secret123")
        category = Category.objects.create(code="SOCIAL", name_fa="دسته اجتماعی", slug="social-category")
        self.product = Product.objects.create(code="SOCIAL-001", name="محصول اجتماعی", slug="social-product", category=category, unit="عدد", is_active=True)
        self.client.force_authenticate(self.user)

    def test_favorite_is_unique_per_customer_and_can_be_removed(self):
        url = f"/api/v1/catalog/products/{self.product.id}/favorite/"
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(ProductFavorite.objects.filter(user=self.user, product=self.product).count(), 1)
        self.assertEqual(self.client.delete(url).json()["is_favorited"], False)

    def test_only_a_customer_with_a_confirmed_purchase_can_review(self):
        url = f"/api/v1/catalog/products/{self.product.id}/reviews/"
        self.assertEqual(self.client.post(url, {"rating": 5, "comment": "خوب بود"}, format="json").status_code, 403)
        order = Order.objects.create(customer=self.user, status=Order.Status.CONFIRMED, subtotal=100, final_amount=100)
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, product_code=self.product.code, unit="عدد", unit_price=Decimal("100"), quantity=1, line_subtotal=Decimal("100"), line_total=Decimal("100"))
        response = self.client.post(url, {"rating": 5, "comment": "خوب بود"}, format="json")
        self.assertEqual(response.status_code, 201)
        review = ProductReview.objects.get(user=self.user, product=self.product)
        self.assertEqual(review.rating, 5)
        self.assertFalse(review.is_published)
