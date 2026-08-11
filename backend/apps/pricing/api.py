from django.core.cache import cache
from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import CurrencyRate, ProductPrice


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ("id", "currency", "rate_to_irr", "rate_date", "source")


class ProductPriceSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductPrice
        fields = ("id", "product_code", "product_name", "amount", "discount_percentage", "currency", "effective_from", "effective_to", "source")


class CurrencyRateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
    permission_classes = (AllowAny,)
    ordering_fields = ("rate_date", "currency")
    ordering = ("-rate_date",)

    def list(self, request, *args, **kwargs):
        cached = cache.get("currency_rates_v1")
        if cached is not None:
            return Response(cached)
        queryset = self.filter_queryset(self.get_queryset())
        data = CurrencyRateSerializer(queryset, many=True).data
        cache.set("currency_rates_v1", data, 300)
        return Response(data)


class ProductPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductPrice.objects.select_related("product")
    serializer_class = ProductPriceSerializer
    permission_classes = (AllowAny,)
    ordering_fields = ("effective_from", "amount")
    ordering = ("-effective_from",)

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset