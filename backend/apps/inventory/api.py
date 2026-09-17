from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Inventory, Issue, Receipt


class StockSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    available_quantity = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)

    class Meta:
        model = Inventory
        fields = ("id", "product_code", "product_name", "on_hand_quantity", "reserved_quantity", "available_quantity", "updated_at")


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.select_related("product").order_by("product__code")
    serializer_class = StockSerializer
    # Internal stock levels: visible to signed-in users only (storefront shows
    # per-product availability via the public catalog serializer instead).
    permission_classes = (IsAuthenticated,)
    ordering_fields = ("product__code", "on_hand_quantity", "reserved_quantity", "updated_at")
    ordering = ("product__code",)


class ReceiptSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Receipt
        fields = ("id", "product_code", "product_name", "quantity", "occurred_at", "reference", "unit_purchase_price_irr", "usd_rate")


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Receipt.objects.select_related("product")
    serializer_class = ReceiptSerializer
    # Purchase prices and supplier references are back-office data.
    permission_classes = (IsAdminUser,)
    ordering_fields = ("occurred_at", "created_at")
    ordering = ("-occurred_at",)


class IssueSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Issue
        fields = ("id", "product_code", "product_name", "quantity", "occurred_at", "reference")


class IssueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Issue.objects.select_related("product")
    serializer_class = IssueSerializer
    # Internal goods-issue history: staff only.
    permission_classes = (IsAdminUser,)
    ordering_fields = ("occurred_at", "created_at")
    ordering = ("-occurred_at",)