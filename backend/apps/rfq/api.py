from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.carts.api import current_cart
from .models import RequestForQuotation, SalesQuotation
from .serializers import RequestForQuotationCreateSerializer, RequestForQuotationReadSerializer, SalesQuotationReadSerializer, SalesQuotationResponseReadSerializer, SalesQuotationResponseWriteSerializer
from .services import generate_quotation_pdf
from .services_response import QuotationResponseError, record_customer_response


def customer_queryset(request):
    return RequestForQuotation.objects.filter(customer=request.user).select_related("customer").prefetch_related("items__product").prefetch_related("quotation")


class PublicFormThrottle(AnonRateThrottle):
    """Limit anonymous RFQ spam."""

    scope = "public_form"


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
@throttle_classes([PublicFormThrottle])
def rfq_collection(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            return Response([])
        return Response(RequestForQuotationReadSerializer(customer_queryset(request)[:100], many=True).data)
    serializer = RequestForQuotationCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    from apps.notifications.services import notify_rfq_submitted
    notify_rfq_submitted(item)
    return Response(RequestForQuotationReadSerializer(item, context={"request": request}).data, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def rfq_cart_context(request):
    """Return only eligible, non-commercial product context from the current cart."""
    cart = current_cart(request, create=False)
    if not cart:
        return Response({"source": "cart", "items": [], "omitted_count": 0, "max_items": 25})
    rows = []
    omitted_count = 0
    for item in cart.items.select_related("product").order_by("id"):
        product = item.product
        if not product.is_active or product.is_obsolete:
            omitted_count += 1
            continue
        if len(rows) >= 25:
            omitted_count += 1
            continue
        rows.append({
            "id": product.id,
            "slug": product.slug,
            "name_fa": product.name,
            "name_en": product.name,
            "sku": product.code,
            "code": product.code,
            "unit": product.unit,
            "quantity": item.quantity,
        })
    return Response({"source": "cart", "items": rows, "omitted_count": omitted_count, "max_items": 25})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rfq_detail(request, reference):
    item = customer_queryset(request).filter(reference=reference).first()
    if not item:
        return Response({"detail": "استعلام قیمت یافت نشد."}, status=404)
    return Response(RequestForQuotationReadSerializer(item).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quotation_collection(request):
    queryset = SalesQuotation.objects.filter(rfq__customer=request.user, status=SalesQuotation.Status.ISSUED).select_related("rfq", "customer_response").prefetch_related("items")
    return Response(SalesQuotationReadSerializer(queryset[:100], many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quotation_detail(request, reference):
    quotation = SalesQuotation.objects.filter(reference=reference, rfq__customer=request.user, status=SalesQuotation.Status.ISSUED).select_related("rfq", "customer_response").prefetch_related("items").first()
    if not quotation:
        return Response({"detail": "پیشنهاد قیمت یافت نشد."}, status=404)
    return Response(SalesQuotationReadSerializer(quotation).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quotation_respond(request, reference):
    serializer = SalesQuotationResponseWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        response = record_customer_response(reference=reference, customer=request.user, **serializer.validated_data)
    except QuotationResponseError as exc:
        status = 404 if exc.not_found else 400
        return Response({"detail": exc.messages}, status=status)
    return Response(SalesQuotationResponseReadSerializer(response).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quotation_pdf(request, reference):
    quotation = SalesQuotation.objects.filter(reference=reference, rfq__customer=request.user, status=SalesQuotation.Status.ISSUED).select_related("rfq").prefetch_related("items").first()
    if not quotation:
        return Response({"detail": "پیشنهاد قیمت یافت نشد."}, status=404)
    locale = request.query_params.get("locale", "fa") if request.query_params.get("locale") in ("fa", "en") else "fa"
    pdf = generate_quotation_pdf(quotation, locale=locale)
    return FileResponse(__import__("io").BytesIO(pdf), as_attachment=True, filename=f"quotation-{quotation.reference}.pdf", content_type="application/pdf")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quotation_convert_to_order(request, reference):
    quotation = SalesQuotation.objects.filter(reference=reference, rfq__customer=request.user, status=SalesQuotation.Status.ISSUED).select_related("rfq").prefetch_related("items__product").first()
    if not quotation:
        return Response({"detail": "پیشنهاد قیمت یافت نشد یا منقضی شده است."}, status=404)
    if quotation.expires_at and quotation.expires_at < timezone.now():
        return Response({"detail": "مهلت اعتبار این پیشنهاد قیمت به پایان رسیده است."}, status=409)

    from decimal import Decimal
    from django.db import transaction
    from apps.orders.models import Order, OrderItem, Payment
    import secrets

    with transaction.atomic():
        order_number = f"ORD-RFQ-{timezone.now().strftime('%Y%m%d')}-{secrets.randbelow(1000000):06d}"
        subtotal = sum(item.line_total for item in quotation.items.all())
        discount_amount = Decimal("0")
        shipping_cost = Decimal("0")
        final_amount = subtotal

        order = Order.objects.create(
            order_number=order_number,
            customer=request.user,
            status=Order.Status.PENDING_PAYMENT,
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_cost=shipping_cost,
            final_amount=final_amount,
            customer_first_name=request.user.first_name or quotation.rfq.contact_name,
            customer_last_name=request.user.last_name or "",
            customer_email=request.user.email or quotation.rfq.email,
            customer_phone=request.user.phone or quotation.rfq.phone,
            customer_company_name=quotation.rfq.company_name or getattr(request.user, "company_name", ""),
            customer_national_id=getattr(request.user, "national_id", ""),
            shipping_province=getattr(request.user, "province", ""),
            shipping_city=getattr(request.user, "city", ""),
            shipping_postal_code=getattr(request.user, "postal_code", ""),
            shipping_address=getattr(request.user, "address", ""),
        )

        for q_item in quotation.items.all():
            OrderItem.objects.create(
                order=order,
                product=q_item.product,
                product_name=q_item.product_name_snapshot,
                product_code=q_item.product_code_snapshot,
                unit=q_item.product.unit if q_item.product else "عدد",
                unit_price=q_item.unit_price,
                quantity=q_item.quantity,
                discount_amount=Decimal("0"),
                line_subtotal=q_item.line_total,
                line_total=q_item.line_total,
            )

        payment = Payment.objects.create(
            order=order,
            gateway="mock_zarinpal",
            amount=order.final_amount,
            status=Payment.Status.PENDING,
        )

        try:
            record_customer_response(reference=reference, customer=request.user, decision="accept", note="تبدیل سیستمی پیشنهاد قیمت به سفارش قطعی")
        except Exception:
            pass

    return Response({
        "detail": "پیشنهاد قیمت با موفقیت به سفارش قطعی تبدیل شد.",
        "order_id": order.id,
        "order_number": order.order_number,
        "payment_id": payment.id,
        "payment_url": f"/payment/{payment.id}",
    }, status=201)
