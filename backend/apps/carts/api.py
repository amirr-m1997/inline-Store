from decimal import Decimal
from datetime import timedelta

import csv

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.catalog.serializers import ProductSerializer
from apps.catalog.models import Product
from apps.inventory.models import Inventory, Reservation
from apps.accounts.models import CustomerAddress, normalize_iranian_phone
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.orders.models import Order, OrderItem, Payment
from .models import Cart, CartItem, DiscountCode


class CartCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = (
            "customer_first_name", "customer_last_name", "customer_email", "customer_phone",
            "customer_company_name", "customer_national_id", "shipping_province", "shipping_city",
            "shipping_postal_code", "shipping_address",
        )

    def validate_customer_phone(self, value):
        compact = value.replace(" ", "").replace("-", "")
        if value and (not compact.lstrip("+").isdigit() or len(compact) < 10):
            raise serializers.ValidationError("شماره تماس معتبر نیست.")
        request = self.context.get("request")
        if value and request and request.user.is_authenticated:
            try:
                normalized = normalize_iranian_phone(value)
            except DjangoValidationError:
                normalized = None
            if normalized and get_user_model().objects.exclude(pk=request.user.pk).filter(phone=normalized).exists():
                raise serializers.ValidationError("این شماره تماس قبلاً برای حساب دیگری ثبت شده است.")
        return value

    def validate_customer_email(self, value):
        value = value.strip().lower() if value else value
        request = self.context.get("request")
        if value and request and request.user.is_authenticated:
            user_model = get_user_model()
            if user_model.objects.exclude(pk=request.user.pk).filter(email=value).exists():
                raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value

    def validate_shipping_postal_code(self, value):
        compact = value.replace("-", "").replace(" ", "")
        if value and (not compact.isdigit() or len(compact) != 10):
            raise serializers.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return compact


def _fill_customer_from_user(cart, user):
    mapping = {
        "customer_first_name": "first_name", "customer_last_name": "last_name",
        "customer_email": "email", "customer_phone": "phone", "customer_company_name": "company_name",
        "customer_national_id": "national_id", "shipping_province": "province", "shipping_city": "city",
        "shipping_postal_code": "postal_code", "shipping_address": "address",
    }
    changed = []
    for cart_field, user_field in mapping.items():
        if not getattr(cart, cart_field) and getattr(user, user_field, ""):
            setattr(cart, cart_field, getattr(user, user_field))
            changed.append(cart_field)
    if changed:
        cart.save(update_fields=changed + ["updated_at"])


def _save_customer_to_profile(cart, user):
    """Copy cart contact data without violating the stricter User phone field."""
    reverse_mapping = {
        "customer_first_name": "first_name", "customer_last_name": "last_name",
        "customer_email": "email", "customer_company_name": "company_name",
        "customer_national_id": "national_id", "shipping_province": "province",
        "shipping_city": "city", "shipping_postal_code": "postal_code",
        "shipping_address": "address",
    }
    update_fields = []
    for cart_field, user_field in reverse_mapping.items():
        setattr(user, user_field, getattr(cart, cart_field))
        update_fields.append(user_field)
    try:
        normalized_phone = normalize_iranian_phone(cart.customer_phone)
    except DjangoValidationError:
        normalized_phone = None
    if normalized_phone:
        user.phone = normalized_phone
        update_fields.append("phone")
    user.save(update_fields=update_fields + ["updated_at"])


def _merge_guest_cart(user_cart, guest_cart):
    if not user_cart.discount_code_id and guest_cart.discount_code_id:
        user_cart.discount_code_id = guest_cart.discount_code_id
        user_cart.save(update_fields=("discount_code", "updated_at"))
    for guest_item in guest_cart.items.select_related("product__inventory"):
        item, _ = CartItem.objects.get_or_create(cart=user_cart, product=guest_item.product, defaults={"quantity": 0})
        available = getattr(getattr(guest_item.product, "inventory", None), "available_quantity", 0)
        item.quantity = min(item.quantity + guest_item.quantity, max(available, 0))
        if item.quantity:
            item.save(update_fields=["quantity", "updated_at"])
    guest_cart.delete()


def current_cart(request, create=True):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, status=Cart.Status.ACTIVE).first()
        if cart is None:
            if not create: return None
            cart = Cart.objects.create(user=request.user)
        token = request.headers.get("X-Guest-Token")
        if token:
            guest_cart = Cart.objects.filter(guest_token=token, user__isnull=True, status=Cart.Status.ACTIVE).exclude(pk=cart.pk).first()
            if guest_cart:
                _merge_guest_cart(cart, guest_cart)
        _fill_customer_from_user(cart, request.user)
        return cart
    token = request.headers.get("X-Guest-Token")
    if token:
        try: return Cart.objects.get(guest_token=token, status=Cart.Status.ACTIVE)
        except Cart.DoesNotExist: pass
    return Cart.objects.create() if create else None


def cart_payload(cart):
    items = list(cart.items.select_related("product", "product__category", "product__inventory").prefetch_related("product__images"))
    rows, total = [], Decimal("0")
    for item in items:
        product = ProductSerializer(item.product).data
        price = product.get("price")
        if price:
            line_total = Decimal(item.quantity) * Decimal(price["final_amount"]).quantize(Decimal("0.01"))
            total += line_total
        else:
            line_total = None
        rows.append({"id": item.id, "quantity": item.quantity, "product": product, "line_total": str(line_total) if line_total is not None else None})
    subtotal = total
    coupon = cart.discount_code
    now = timezone.now()
    coupon_valid = bool(coupon and coupon.is_active and coupon.valid_from <= now and (coupon.valid_until is None or coupon.valid_until >= now) and (coupon.max_uses is None or coupon.usage_count < coupon.max_uses) and subtotal >= coupon.minimum_order_amount)
    percentage = coupon.percentage if coupon_valid else Decimal("0")
    discount_amount = (subtotal * percentage / Decimal("100")).quantize(Decimal("0.01"))
    final_total = max(Decimal("0"), subtotal - discount_amount)
    customer = CartCustomerSerializer(cart).data
    complete = all(customer[field] for field in ("customer_first_name", "customer_last_name", "customer_phone", "shipping_province", "shipping_city", "shipping_postal_code", "shipping_address"))
    return {"id": cart.id, "guest_token": str(cart.guest_token) if cart.guest_token else None, "items": rows, "subtotal": str(subtotal), "discount_amount": str(discount_amount), "total": str(final_total), "discount": {"code": coupon.code, "percentage": str(percentage)} if coupon_valid else None, "customer": customer, "customer_complete": complete}


@api_view(["GET", "PATCH"])
@permission_classes([permissions.AllowAny])
def cart_detail(request):
    cart = current_cart(request)
    if request.method == "PATCH":
        serializer = CartCustomerSerializer(cart, data=request.data.get("customer", request.data), partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if request.user.is_authenticated and request.data.get("save_to_profile", True):
            _save_customer_to_profile(cart, request.user)
            address_fields = {
                "recipient_name": f"{cart.customer_first_name} {cart.customer_last_name}".strip(),
                "recipient_phone": None,
                "province": cart.shipping_province, "city": cart.shipping_city,
                "postal_code": cart.shipping_postal_code, "address": cart.shipping_address,
            }
            try:
                address_fields["recipient_phone"] = normalize_iranian_phone(cart.customer_phone)
            except DjangoValidationError:
                pass
            if all(address_fields.values()):
                CustomerAddress.objects.update_or_create(
                    user=request.user, is_default=True,
                    defaults={"title": "نشانی پیش‌فرض", **address_fields},
                )
    return Response(cart_payload(cart))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def add_item(request):
    product_id = request.data.get("product_id")
    try: quantity = int(request.data.get("quantity", 1))
    except (TypeError, ValueError): return Response({"detail": "Quantity must be an integer."}, status=400)
    if quantity < 1: return Response({"detail": "Quantity must be positive."}, status=400)
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if not product: return Response({"detail": "Product not found."}, status=404)
    with transaction.atomic():
        inventory = Inventory.objects.select_for_update().filter(product=product).first()
        cart = current_cart(request); item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 0})
        if not inventory or inventory.available_quantity < item.quantity + quantity: return Response({"detail": "Insufficient inventory."}, status=400)
        item.quantity += quantity; item.save()
    return Response(cart_payload(cart), status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([permissions.AllowAny])
def cart_item(request, item_id):
    cart = current_cart(request); item = cart.items.filter(pk=item_id).first()
    if not item: return Response({"detail": "Cart item not found."}, status=404)
    if request.method == "DELETE": item.delete(); return Response(status=204)
    try: quantity = int(request.data.get("quantity", 0))
    except (TypeError, ValueError): return Response({"detail": "Quantity must be an integer."}, status=400)
    if quantity < 1: item.delete()
    else:
        inventory = Inventory.objects.filter(product=item.product).first()
        if not inventory or quantity > inventory.available_quantity:
            return Response({"detail": "Insufficient inventory."}, status=400)
        item.quantity = quantity; item.save()
    return Response(cart_payload(cart))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def checkout(request):
    cart = current_cart(request, create=False)
    if not cart or cart.status != Cart.Status.ACTIVE:
        return Response({"detail": "سبد خرید فعال پیدا نشد."}, status=400)
    required = ("customer_first_name", "customer_last_name", "customer_phone", "shipping_province", "shipping_city", "shipping_postal_code", "shipping_address")
    if any(not getattr(cart, field) for field in required):
        return Response({"detail": "اطلاعات مشتری و نشانی تحویل کامل نیست."}, status=400)
    items = list(cart.items.select_related("product"))
    if not items:
        return Response({"detail": "سبد خرید خالی است."}, status=400)
    with transaction.atomic():
        locked_cart = Cart.objects.select_for_update().get(pk=cart.pk)
        if locked_cart.status != Cart.Status.ACTIVE:
            return Response({"detail": "این سبد قبلاً ثبت شده است."}, status=409)
        inventories = {inventory.product_id: inventory for inventory in Inventory.objects.select_for_update().filter(product_id__in=[item.product_id for item in items])}
        totals = cart_payload(locked_cart)
        coupon = None
        if locked_cart.discount_code_id:
            coupon = DiscountCode.objects.select_for_update().get(pk=locked_cart.discount_code_id)
            now = timezone.now()
            if not coupon.is_active or coupon.valid_from > now or (coupon.valid_until and coupon.valid_until < now) or (coupon.max_uses is not None and coupon.usage_count >= coupon.max_uses) or Decimal(totals["subtotal"]) < coupon.minimum_order_amount:
                return Response({"detail": "کد تخفیف دیگر معتبر نیست؛ لطفاً سبد را به‌روزرسانی کنید."}, status=400)
        for item in items:
            inventory = inventories.get(item.product_id)
            if not inventory or inventory.available_quantity < item.quantity:
                return Response({"detail": f"موجودی «{item.product.name}» برای ثبت سفارش کافی نیست."}, status=400)
        expires_at = timezone.now() + timedelta(hours=24)
        order = Order.objects.create(
            order_number=f"MEHR-{locked_cart.id:08d}", customer=locked_cart.user,
            source_cart=locked_cart, status=Order.Status.PENDING_PAYMENT,
            subtotal=Decimal(totals["subtotal"]),
            discount_code=totals["discount"]["code"] if totals["discount"] else "",
            discount_percentage=Decimal(totals["discount"]["percentage"]) if totals["discount"] else 0,
            discount_amount=Decimal(totals["discount_amount"]), final_amount=Decimal(totals["total"]),
            customer_first_name=locked_cart.customer_first_name, customer_last_name=locked_cart.customer_last_name,
            customer_email=locked_cart.customer_email, customer_phone=locked_cart.customer_phone,
            customer_company_name=locked_cart.customer_company_name, customer_national_id=locked_cart.customer_national_id,
            shipping_province=locked_cart.shipping_province, shipping_city=locked_cart.shipping_city,
            shipping_postal_code=locked_cart.shipping_postal_code, shipping_address=locked_cart.shipping_address,
        )
        for item in items:
            inventory = inventories[item.product_id]
            product_data = ProductSerializer(item.product).data
            price = product_data.get("price") or {}
            original_price = Decimal(price.get("original_amount") or 0)
            final_price = Decimal(price.get("final_amount") or 0)
            line_subtotal = original_price * item.quantity
            line_total = final_price * item.quantity
            order_item = OrderItem.objects.create(
                order=order, product=item.product, product_name=item.product.name,
                product_code=item.product.code, unit=item.product.unit,
                unit_price=original_price, quantity=item.quantity,
                discount_percentage=Decimal(price.get("discount_percentage") or 0),
                discount_amount=line_subtotal - line_total,
                line_subtotal=line_subtotal, line_total=line_total,
            )
            inventory.reserved_quantity += item.quantity
            inventory.save(update_fields=("reserved_quantity", "updated_at"))
            Reservation.objects.create(product=item.product, cart_item=item, order_item=order_item, quantity=item.quantity, expires_at=expires_at)
        locked_cart.status = Cart.Status.CHECKED_OUT
        locked_cart.discount_percentage = Decimal(totals["discount"]["percentage"]) if totals["discount"] else 0
        locked_cart.discount_amount = Decimal(totals["discount_amount"])
        locked_cart.final_total = Decimal(totals["total"])
        locked_cart.save(update_fields=("status", "discount_percentage", "discount_amount", "final_total", "updated_at"))
        payment = Payment.objects.create(order=order, gateway="mock_zarinpal", amount=order.final_amount, status=Payment.Status.PENDING)
    return Response({"detail": "سفارش ایجاد شد؛ برای تکمیل به صفحه پرداخت بروید.", "order_reference": order.order_number, "order_id": order.id, "payment_id": payment.id, "payment_url": f"/fa/payment/{payment.id}", "reserved_until": expires_at})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def orders(request):
    carts = Cart.objects.filter(user=request.user, status=Cart.Status.CHECKED_OUT).prefetch_related("items__product").order_by("-updated_at")
    payload = []
    for cart in carts:
        payload.append({
            "id": cart.id, "reference": f"MEHR-{cart.id:08d}", "status": cart.status,
            "created_at": cart.created_at, "submitted_at": cart.updated_at,
            "shipping_address": cart.shipping_address, "subtotal": str(cart.final_total + cart.discount_amount),
            "discount_code": cart.discount_code.code if cart.discount_code else None, "discount_percentage": str(cart.discount_percentage),
            "discount_amount": str(cart.discount_amount), "total": str(cart.final_total),
            "items": [{"id": item.id, "product_name": item.product.name, "product_slug": item.product.slug, "quantity": item.quantity, "unit": item.product.unit} for item in cart.items.all()],
        })
    return Response(payload)


@api_view(["POST", "DELETE"])
@permission_classes([permissions.AllowAny])
def discount(request):
    cart = current_cart(request)
    if request.method == "DELETE":
        cart.discount_code = None; cart.save(update_fields=("discount_code", "updated_at"))
        return Response(cart_payload(cart))
    code = str(request.data.get("code", "")).strip().upper()
    coupon = DiscountCode.objects.filter(code__iexact=code).first()
    if not coupon:
        return Response({"detail": "کد تخفیف معتبر نیست."}, status=400)
    now = timezone.now()
    if not coupon.is_active or coupon.valid_from > now or (coupon.valid_until and coupon.valid_until < now):
        return Response({"detail": "زمان استفاده از این کد تخفیف به پایان رسیده است."}, status=400)
    if coupon.max_uses is not None and coupon.usage_count >= coupon.max_uses:
        return Response({"detail": "ظرفیت استفاده از این کد تخفیف تکمیل شده است."}, status=400)
    cart.discount_code = coupon; cart.save(update_fields=("discount_code", "updated_at"))
    payload = cart_payload(cart)
    if Decimal(payload["subtotal"]) < coupon.minimum_order_amount:
        cart.discount_code = None; cart.save(update_fields=("discount_code", "updated_at"))
        return Response({"detail": f"حداقل مبلغ سفارش برای این کد {coupon.minimum_order_amount:,.0f} ریال است."}, status=400)
    return Response(payload)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def cart_export_csv(request):
    cart = current_cart(request)
    items = list(cart.items.select_related("product", "product__category", "product__inventory").prefetch_related("product__images"))
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="cart.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["code", "name", "unit", "quantity", "on_hand", "reserved", "available", "line_total_irr"])
    total = Decimal("0")
    for item in items:
        data = ProductSerializer(item.product).data
        price = data.get("price")
        line_total = Decimal(item.quantity) * Decimal(price["final_amount"]).quantize(Decimal("0.01")) if price else None
        if line_total is not None:
            total += line_total
        writer.writerow([
            data["code"], data["name"], data["unit"], item.quantity,
            data.get("on_hand_quantity") if data.get("on_hand_quantity") is not None else "",
            data.get("reserved_quantity") if data.get("reserved_quantity") is not None else "",
            data.get("available_quantity") if data.get("available_quantity") is not None else "",
            str(line_total) if line_total is not None else "",
        ])
    writer.writerow([])
    writer.writerow(["TOTAL", "", "", "", "", "", "", str(total)])
    return response
