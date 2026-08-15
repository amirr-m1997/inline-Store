from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Product
from .models import RequestForQuotation, RequestForQuotationItem, SalesQuotation, SalesQuotationItem, SalesQuotationResponse


def validate_contact_phone(value):
    compact = "".join(value.split()).replace("-", "").replace("(", "").replace(")", "")
    if not compact.lstrip("+").isdigit() or len(compact.lstrip("+")) < 7:
        raise serializers.ValidationError("شماره تماس معتبر نیست.")
    return compact


class RfqProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "code", "name", "slug", "unit")


class RequestForQuotationItemReadSerializer(serializers.ModelSerializer):
    product = RfqProductSummarySerializer(read_only=True)

    class Meta:
        model = RequestForQuotationItem
        fields = ("product", "requested_quantity", "customer_note", "product_code_snapshot", "product_name_snapshot")


class RequestForQuotationReadSerializer(serializers.ModelSerializer):
    items = RequestForQuotationItemReadSerializer(many=True, read_only=True)
    quotation_reference = serializers.SerializerMethodField()
    quotation_response = serializers.SerializerMethodField()

    class Meta:
        model = RequestForQuotation
        fields = ("reference", "company_name", "contact_name", "phone", "email", "subject", "message", "preferred_contact_method", "status", "created_at", "updated_at", "items", "quotation_reference", "quotation_response")
        read_only_fields = fields

    def get_quotation_reference(self, obj):
        quotation = getattr(obj, "quotation", None)
        return quotation.reference if quotation and quotation.status == SalesQuotation.Status.ISSUED else None

    def get_quotation_response(self, obj):
        quotation = getattr(obj, "quotation", None)
        response = getattr(quotation, "customer_response", None) if quotation and quotation.status == SalesQuotation.Status.ISSUED else None
        return {"response": response.response, "response_at": response.response_at} if response else None


class SalesQuotationItemReadSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = SalesQuotationItem
        fields = ("product_name_snapshot", "product_code_snapshot", "quantity", "unit_price", "line_total")

    def get_line_total(self, obj):
        return str(obj.line_total)


class SalesQuotationReadSerializer(serializers.ModelSerializer):
    rfq_reference = serializers.CharField(source="rfq.reference", read_only=True)
    items = SalesQuotationItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    customer_response = serializers.SerializerMethodField()

    class Meta:
        model = SalesQuotation
        fields = ("reference", "rfq_reference", "status", "currency", "issued_at", "expires_at", "public_note", "items", "subtotal", "customer_response")
        read_only_fields = fields

    def get_subtotal(self, obj):
        return str(obj.subtotal)

    def get_customer_response(self, obj):
        try:
            response = obj.customer_response
        except SalesQuotationResponse.DoesNotExist:
            response = None
        return {
            "response": response.response,
            "note": response.note,
            "response_at": response.response_at,
        } if response else {"response": "pending", "note": "", "response_at": None}


class SalesQuotationResponseReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesQuotationResponse
        fields = ("response", "response_at")
        read_only_fields = fields


class SalesQuotationResponseWriteSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=(
        SalesQuotationResponse.ResponseType.ACCEPTED,
        SalesQuotationResponse.ResponseType.REJECTED,
        SalesQuotationResponse.ResponseType.REVISION_REQUESTED,
    ))
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if attrs["response"] == SalesQuotationResponse.ResponseType.REVISION_REQUESTED and not attrs.get("note", "").strip():
            raise serializers.ValidationError({"note": "برای درخواست اصلاح، توضیحات الزامی است."})
        return attrs


class RequestForQuotationItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    requested_quantity = serializers.IntegerField(min_value=1, max_value=1_000_000)
    customer_note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_product(self, product):
        if not product.is_active:
            raise serializers.ValidationError("محصول انتخاب‌شده برای استعلام عمومی فعال نیست.")
        return product


class RequestForQuotationCreateSerializer(serializers.ModelSerializer):
    items = RequestForQuotationItemWriteSerializer(many=True, required=False)

    class Meta:
        model = RequestForQuotation
        fields = ("company_name", "contact_name", "phone", "email", "subject", "message", "preferred_contact_method", "items")

    def validate_phone(self, value):
        return validate_contact_phone(value)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        items = attrs.get("items", [])
        if len(items) > 25:
            raise serializers.ValidationError({"items": "حداکثر ۲۵ قلم در هر استعلام مجاز است."})
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError({"items": "یک محصول نمی‌تواند در چند قلم تکرار شود."})
        message = (attrs.get("message") or "").strip()
        if not message and not items:
            raise serializers.ValidationError({"message": "شرح نیاز یا حداقل یک قلم محصول لازم است."})
        if not attrs.get("contact_name", "").strip():
            raise serializers.ValidationError({"contact_name": "نام تماس الزامی است."})
        if not attrs.get("phone") and not attrs.get("email"):
            raise serializers.ValidationError({"phone": "حداقل یکی از تلفن یا ایمیل الزامی است."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        request = self.context.get("request")
        customer = request.user if request and request.user.is_authenticated else None
        rfq = RequestForQuotation.objects.create(customer=customer, **validated_data)
        RequestForQuotationItem.objects.bulk_create([
            RequestForQuotationItem(
                rfq=rfq, product=item["product"], requested_quantity=item["requested_quantity"],
                customer_note=item.get("customer_note", ""), product_code_snapshot=item["product"].code,
                product_name_snapshot=item["product"].name,
            ) for item in items
        ])
        return rfq
