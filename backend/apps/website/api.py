from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.db.models import Prefetch

from apps.company.models import CompanyInfo
from .models import ContactMessage, CustomerFeedback, CustomerSupportRequest, FooterLink, FooterSection, SiteNavigation, TrustBadge, WarrantyPolicy, WarrantyRegistration


class SiteNavigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteNavigation
        fields = ("id", "title_fa", "title_en", "url", "order", "icon")


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ("full_name", "phone", "email", "subject", "message")

    def validate_phone(self, value):
        compact = value.replace(" ", "").replace("-", "")
        if not compact.lstrip("+").isdigit() or len(compact) < 10:
            raise serializers.ValidationError("شماره تماس معتبر نیست.")
        return value

class WarrantyPolicySerializer(serializers.ModelSerializer):
    class Meta: model = WarrantyPolicy; fields = ("id", "title_fa", "title_en", "body_fa", "body_en", "registration_enabled")

class WarrantyRegistrationSerializer(serializers.ModelSerializer):
    class Meta: model = WarrantyRegistration; fields = ("reference", "product", "order", "serial_number", "purchase_date", "full_name", "phone", "email", "notes", "status", "submitted_at"); read_only_fields = ("reference", "status", "submitted_at")
    def validate_phone(self, value): return ContactMessageSerializer().validate_phone(value)
    def validate_order(self, value):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or value.customer_id != request.user.id:
            raise serializers.ValidationError("سفارش انتخاب‌شده قابل استفاده نیست.")
        return value

class SupportRequestSerializer(serializers.ModelSerializer):
    class Meta: model = CustomerSupportRequest; fields = ("reference", "request_type", "product", "order", "full_name", "phone", "email", "subject", "message", "status", "submitted_at"); read_only_fields = ("reference", "status", "submitted_at")
    def validate_phone(self, value): return ContactMessageSerializer().validate_phone(value)
    def validate_order(self, value):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or value.customer_id != request.user.id:
            raise serializers.ValidationError("سفارش انتخاب‌شده قابل استفاده نیست.")
        return value

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta: model = CustomerFeedback; fields = ("id", "order", "feedback_type", "rating", "message", "contact_permission", "submitted_at"); read_only_fields = ("id", "submitted_at")
    def validate_rating(self, value):
        if value is not None and not 1 <= value <= 5: raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


@api_view(["GET"])
@permission_classes([AllowAny])
def navigation_list(request):
    items = SiteNavigation.objects.filter(is_active=True)
    return Response(SiteNavigationSerializer(items, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def contact_message_create(request):
    serializer = ContactMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "پیام شما با موفقیت ثبت شد."}, status=201)

@api_view(["GET"])
@permission_classes([AllowAny])
def warranty_policy(request):
    item = WarrantyPolicy.objects.filter(is_published=True).order_by("-id").first()
    return Response(WarrantyPolicySerializer(item).data if item else None)

@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def warranty_registrations(request):
    if request.method == "GET":
        if not request.user.is_authenticated: return Response([], status=200)
        return Response(WarrantyRegistrationSerializer(WarrantyRegistration.objects.filter(customer=request.user), many=True).data)
    serializer = WarrantyRegistrationSerializer(data=request.data, context={"request": request}); serializer.is_valid(raise_exception=True)
    item = serializer.save(customer=request.user if request.user.is_authenticated else None)
    return Response(WarrantyRegistrationSerializer(item).data, status=201)

@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def support_requests(request):
    if request.method == "GET":
        if not request.user.is_authenticated: return Response([], status=200)
        return Response(SupportRequestSerializer(CustomerSupportRequest.objects.filter(customer=request.user), many=True).data)
    serializer = SupportRequestSerializer(data=request.data, context={"request": request}); serializer.is_valid(raise_exception=True)
    item = serializer.save(customer=request.user if request.user.is_authenticated else None)
    return Response(SupportRequestSerializer(item).data, status=201)

@api_view(["POST"])
@permission_classes([AllowAny])
def feedback_create(request):
    serializer = FeedbackSerializer(data=request.data); serializer.is_valid(raise_exception=True)
    item = serializer.save(customer=request.user if request.user.is_authenticated else None)
    return Response(FeedbackSerializer(item).data, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def footer_detail(request):
    company = CompanyInfo.objects.first()
    sections = FooterSection.objects.filter(is_active=True).prefetch_related(
        Prefetch("links", queryset=FooterLink.objects.filter(is_active=True).order_by("order", "id"))
    )
    badges = TrustBadge.objects.filter(is_active=True, image__isnull=False).exclude(image="")
    company_payload = None
    copyright_text = ""
    if company:
        company_payload = {
            "name_fa": company.name_fa,
            "logo": company.logo.url if company.logo else None,
            "description": company.description,
            "phone": company.phone,
            "mobile": company.mobile,
            "email": company.email,
            "address": company.address,
            "website": company.website,
        }
        copyright_text = company.footer_copyright_fa
    return Response({
        "company": company_payload,
        "sections": [{
            "id": section.id,
            "title": section.title_fa,
            "links": [{
                "id": link.id, "title": link.title_fa, "url": link.url,
                "open_in_new_tab": link.open_in_new_tab,
            } for link in section.links.all()],
        } for section in sections],
        "trust_badges": [{
            "id": badge.id, "title": badge.title_fa,
            "image": badge.image.url, "url": badge.url,
            "alt": badge.alt_fa or badge.title_fa,
        } for badge in badges],
        "copyright": copyright_text,
    })
