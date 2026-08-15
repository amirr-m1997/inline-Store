from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.carts.api import current_cart
from .models import RequestForQuotation, SalesQuotation
from .serializers import RequestForQuotationCreateSerializer, RequestForQuotationReadSerializer, SalesQuotationReadSerializer, SalesQuotationResponseReadSerializer, SalesQuotationResponseWriteSerializer
from .services import generate_quotation_pdf
from .services_response import QuotationResponseError, record_customer_response


def customer_queryset(request):
    return RequestForQuotation.objects.filter(customer=request.user).select_related("customer").prefetch_related("items__product").prefetch_related("quotation")


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
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
        if not product.is_active:
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
