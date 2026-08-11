import secrets

from django.db import transaction
from django.db.models import F
from django.http import FileResponse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.carts.models import DiscountCode
from apps.inventory.models import Inventory, Issue, Reservation
from .models import Order, Payment, ProformaRequest
from .services import create_invoice, email_invoice, ensure_invoice_pdf


def accessible_payment(request, payment_id):
    payment = Payment.objects.select_related("order__source_cart", "order__customer").filter(pk=payment_id).first()
    if not payment:
        return None
    order = payment.order
    if request.user.is_authenticated:
        return payment if order.customer_id == request.user.id else None
    token = request.headers.get("X-Guest-Token", "")
    return payment if token and order.source_cart and str(order.source_cart.guest_token) == token else None


def payment_payload(payment):
    return {
        "id": payment.id, "gateway": payment.gateway, "amount": str(payment.amount),
        "authority": payment.authority, "reference_id": payment.reference_id,
        "status": payment.status, "verified_at": payment.verified_at,
        "order": {"id": payment.order_id, "order_number": payment.order.order_number, "status": payment.order.status},
    }


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def payment_detail(request, payment_id):
    payment = accessible_payment(request, payment_id)
    if not payment: return Response({"detail": "پرداخت یافت نشد."}, status=404)
    return Response(payment_payload(payment))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def mock_complete(request, payment_id):
    visible = accessible_payment(request, payment_id)
    if not visible: return Response({"detail": "پرداخت یافت نشد."}, status=404)
    outcome = request.data.get("outcome", "success")
    if outcome not in ("success", "failed", "cancelled"):
        return Response({"detail": "نتیجه پرداخت نامعتبر است."}, status=400)
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("order__source_cart").get(pk=visible.pk)
        order = Order.objects.select_for_update().get(pk=payment.order_id)
        if payment.status == Payment.Status.VERIFIED:
            return Response(payment_payload(payment))
        if order.status != Order.Status.PENDING_PAYMENT:
            return Response({"detail": "این سفارش دیگر قابل پرداخت نیست."}, status=409)
        if outcome != "success":
            payment.status = Payment.Status.CANCELLED if outcome == "cancelled" else Payment.Status.FAILED
            payment.save(update_fields=("status",))
            return Response(payment_payload(payment))

        reservations = list(Reservation.objects.select_for_update().filter(order_item__order=order, status=Reservation.Status.ACTIVE).select_related("product"))
        inventories = {item.product_id: item for item in Inventory.objects.select_for_update().filter(product_id__in=[reservation.product_id for reservation in reservations])}
        for reservation in reservations:
            inventory = inventories.get(reservation.product_id)
            if not inventory or inventory.reserved_quantity < reservation.quantity or inventory.on_hand_quantity < reservation.quantity:
                return Response({"detail": "موجودی رزروشده سفارش معتبر نیست."}, status=409)
        reference = f"MOCK-{secrets.token_hex(5).upper()}"
        for reservation in reservations:
            inventory = inventories[reservation.product_id]
            inventory.reserved_quantity -= reservation.quantity
            inventory.on_hand_quantity -= reservation.quantity
            inventory.save(update_fields=("reserved_quantity", "on_hand_quantity", "updated_at"))
            reservation.status = Reservation.Status.CONVERTED
            reservation.save(update_fields=("status", "updated_at"))
            Issue.objects.create(product=reservation.product, quantity=reservation.quantity, occurred_at=timezone.now(), reference=reference)
        order.status = Order.Status.CONFIRMED; order.paid_at = timezone.now()
        order.save(update_fields=("status", "paid_at", "updated_at"))
        payment.status = Payment.Status.VERIFIED; payment.reference_id = reference; payment.verified_at = timezone.now()
        payment.authority = payment.authority or f"MOCK-AUTH-{payment.id}"
        payment.save(update_fields=("status", "reference_id", "verified_at", "authority"))
        if order.discount_code:
            DiscountCode.objects.filter(code=order.discount_code).update(usage_count=F("usage_count") + 1)
    create_invoice(order)
    return Response(payment_payload(payment))


def _owned_order(request, order_id):
    return Order.objects.filter(pk=order_id, customer=request.user).prefetch_related("items", "status_history").first()


def _order_payload(order, detailed=False):
    data = {"id": order.id, "order_number": order.order_number, "status": order.status,
            "status_label": order.get_status_display(), "created_at": order.created_at,
            "final_amount": str(order.final_amount), "currency": order.currency,
            "items_count": sum(item.quantity for item in order.items.all())}
    if detailed:
        proforma = ProformaRequest.objects.filter(order=order).first()
        data.update({
            "subtotal": str(order.subtotal), "discount_amount": str(order.discount_amount),
            "shipping_cost": str(order.shipping_cost), "paid_at": order.paid_at,
            "shipped_at": order.shipped_at, "delivered_at": order.delivered_at,
            "shipping_address": "، ".join(filter(None, (order.shipping_province, order.shipping_city, order.shipping_address))),
            "items": [{"id": item.id, "product_name": item.product_name, "product_code": item.product_code,
                       "unit": item.unit, "unit_price": str(item.unit_price), "quantity": item.quantity,
                       "discount_amount": str(item.discount_amount), "line_total": str(item.line_total)} for item in order.items.all()],
            "timeline": [{"status": row.status, "status_label": row.get_status_display(), "description": row.description,
                          "created_at": row.created_at} for row in order.status_history.all()],
            "invoice": {"number": f"INV-{order.order_number}", "download_url": f"/api/customer/orders/{order.id}/invoice/"},
            "proforma_request": None if not proforma else {"status": proforma.status, "status_label": proforma.get_status_display(),
                "customer_note": proforma.customer_note, "admin_note": proforma.admin_note, "requested_at": proforma.requested_at},
        })
    return data


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def customer_orders(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related("items").order_by("-created_at")
    return Response([_order_payload(order) for order in orders])


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def customer_order_detail(request, order_id):
    order = _owned_order(request, order_id)
    if not order: return Response({"detail": "سفارش یافت نشد."}, status=404)
    return Response(_order_payload(order, detailed=True))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def invoice_download(request, order_id):
    order = _owned_order(request, order_id)
    if not order: return Response({"detail": "سفارش یافت نشد."}, status=404)
    invoice = ensure_invoice_pdf(create_invoice(order))
    preview = request.query_params.get("preview") == "1"
    return FileResponse(invoice.pdf_file.open("rb"), as_attachment=not preview, filename=f"{invoice.invoice_number}.pdf", content_type="application/pdf")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def invoice_send(request, order_id):
    order = _owned_order(request, order_id)
    if not order: return Response({"detail": "سفارش یافت نشد."}, status=404)
    recipient = request.user.email or order.customer_email
    if not recipient: return Response({"detail": "برای ارسال فاکتور ابتدا ایمیل حساب را ثبت کنید."}, status=400)
    try: email_invoice(create_invoice(order), recipient)
    except Exception: return Response({"detail": "ارسال ایمیل ناموفق بود؛ تنظیمات سرویس ایمیل را بررسی کنید."}, status=503)
    return Response({"detail": "فاکتور با موفقیت ایمیل شد.", "recipient": recipient})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def proforma_request(request, order_id):
    order = _owned_order(request, order_id)
    if not order: return Response({"detail": "سفارش یافت نشد."}, status=404)
    note = str(request.data.get("note", "")).strip()
    if len(note) > 2000: return Response({"detail": "توضیحات نمی‌تواند بیشتر از ۲۰۰۰ نویسه باشد."}, status=400)
    item, created = ProformaRequest.objects.get_or_create(order=order, defaults={"customer": request.user, "customer_note": note})
    if not created:
        return Response({"detail": "درخواست پیش‌فاکتور رسمی قبلاً ثبت شده است.", "status": item.status,
                         "status_label": item.get_status_display(), "requested_at": item.requested_at}, status=409)
    return Response({"detail": "درخواست پیش‌فاکتور رسمی با موفقیت ثبت شد.", "status": item.status,
                     "status_label": item.get_status_display(), "requested_at": item.requested_at}, status=201)
