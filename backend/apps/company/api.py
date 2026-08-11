from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import CompanyAdvantage, CompanyInfo
from rest_framework import serializers


class HeroSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="hero_title_fa")
    slogan = serializers.CharField(source="hero_slogan_fa")
    description = serializers.CharField(source="hero_description_fa")
    hero_image = serializers.SerializerMethodField()
    mobile_hero_image = serializers.SerializerMethodField()
    buttons = serializers.SerializerMethodField()

    class Meta:
        model = CompanyInfo
        fields = ("title", "slogan", "description", "hero_image", "mobile_hero_image", "buttons")

    def image_url(self, value):
        return value.url if value else None

    def get_hero_image(self, obj):
        return self.image_url(obj.hero_image)

    def get_mobile_hero_image(self, obj):
        return self.image_url(obj.mobile_hero_image)

    def get_buttons(self, obj):
        pairs = ((obj.primary_button_text, obj.primary_button_link, "primary"), (obj.secondary_button_text, obj.secondary_button_link, "secondary"))
        return [{"text": text, "link": link, "variant": variant} for text, link, variant in pairs if text and link]


class CompanyAdvantageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAdvantage
        fields = ("id", "title_fa", "title_en", "description_fa", "description_en", "icon", "order")


@api_view(["GET"])
@permission_classes([AllowAny])
def company_detail(request):
    company = CompanyInfo.objects.first()
    if company is None:
        return Response({"detail": "Company information is not available."}, status=404)
    return Response({
        "id": company.id,
        "name_fa": company.name_fa,
        "logo": company.logo.url if company.logo else None,
        "description": company.description,
        "address": company.address,
        "phone": company.phone,
        "mobile": company.mobile,
        "email": company.email,
        "website": company.website,
        "working_hours": company.working_hours,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def hero_detail(request):
    company = CompanyInfo.objects.filter(hero_is_active=True).first()
    if company is None:
        return Response({"detail": "Hero settings are not available."}, status=404)
    return Response(HeroSerializer(company, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def advantage_list(request):
    advantages = CompanyAdvantage.objects.filter(is_active=True)
    return Response(CompanyAdvantageSerializer(advantages, many=True).data)
