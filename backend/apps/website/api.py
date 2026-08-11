from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.db.models import Prefetch

from apps.company.models import CompanyInfo
from .models import ContactMessage, FooterLink, FooterSection, SiteNavigation, TrustBadge


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
