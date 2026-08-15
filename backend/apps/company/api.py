from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Capability, CompanyAdvantage, CompanyCertification, CompanyHonor, CompanyInfo, CompanyLocation, CompanyMilestone, CompanySection, Industry
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


class CompanySectionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = CompanySection
        fields = ("id", "section_type", "title_fa", "title_en", "summary_fa", "summary_en", "body_fa", "body_en", "image", "order")

    def get_image(self, obj):
        return obj.image.url if obj.image else None


class CapabilitySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Capability
        fields = ("id", "slug", "title_fa", "title_en", "summary_fa", "summary_en", "body_fa", "body_en", "icon", "image", "cta_label_fa", "cta_label_en", "cta_url", "seo_title_fa", "seo_title_en", "seo_description_fa", "seo_description_en", "categories", "products", "order")

    def get_image(self, obj):
        return obj.image.url if obj.image else None

    def get_categories(self, obj):
        return list(obj.categories.filter(is_active=True).values("id", "name_fa", "name_en", "slug"))

    def get_products(self, obj):
        return list(obj.products.filter(is_active=True).values("id", "name", "code", "slug"))


class CompanyLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyLocation
        fields = ("id", "location_type", "name_fa", "name_en", "address_fa", "address_en", "phone", "mobile", "email", "working_hours", "website", "latitude", "longitude", "order")


class CompanyMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMilestone
        fields = ("id", "date_label", "title_fa", "title_en", "description_fa", "description_en", "order")


class CompanyCertificationSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = CompanyCertification
        fields = ("id", "title_fa", "title_en", "issuer", "certificate_code", "file", "image", "issued_date", "expiry_date", "verification_status", "order")

    def _url(self, value):
        if not value:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(value.url) if request else value.url

    def get_file(self, obj): return self._url(obj.file)
    def get_image(self, obj): return self._url(obj.image)


class CompanyHonorSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = CompanyHonor
        fields = ("id", "title_fa", "title_en", "issuer", "year_label", "description_fa", "description_en", "image", "file", "order")

    def _url(self, value):
        if not value:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(value.url) if request else value.url

    def get_image(self, obj): return self._url(obj.image)
    def get_file(self, obj): return self._url(obj.file)


class IndustrySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = Industry
        fields = ("id", "slug", "name_fa", "name_en", "description_fa", "description_en", "image", "categories", "products", "capabilities", "order")

    def get_image(self, obj):
        if not obj.image: return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

    def get_categories(self, obj): return list(obj.categories.filter(is_active=True).values("id", "name_fa", "name_en", "slug"))
    def get_products(self, obj): return list(obj.products.filter(is_active=True).values("id", "name", "code", "slug"))
    def get_capabilities(self, obj): return list(obj.capabilities.filter(is_active=True, is_published=True).values("id", "slug", "title_fa", "title_en"))


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


@api_view(["GET"])
@permission_classes([AllowAny])
def company_sections(request):
    sections = CompanySection.objects.filter(is_active=True, is_published=True)
    return Response(CompanySectionSerializer(sections, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def capability_list(request):
    capabilities = Capability.objects.filter(is_active=True, is_published=True)
    return Response(CapabilitySerializer(capabilities, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def capability_detail(request, slug):
    capability = Capability.objects.filter(slug=slug, is_active=True, is_published=True).first()
    if capability is None:
        return Response({"detail": "Not found."}, status=404)
    return Response(CapabilitySerializer(capability, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def company_locations(request):
    items = CompanyLocation.objects.filter(is_active=True, is_published=True)
    return Response(CompanyLocationSerializer(items, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def company_milestones(request):
    items = CompanyMilestone.objects.filter(is_published=True)
    return Response(CompanyMilestoneSerializer(items, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def company_certifications(request):
    items = CompanyCertification.objects.filter(is_published=True, verification_status=CompanyCertification.VerificationStatus.VERIFIED)
    return Response(CompanyCertificationSerializer(items, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def company_honors(request):
    items = CompanyHonor.objects.filter(is_published=True, verification_required=False)
    return Response(CompanyHonorSerializer(items, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def industry_list(request):
    items = Industry.objects.filter(is_active=True, is_published=True)
    return Response(IndustrySerializer(items, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def industry_detail(request, slug):
    item = Industry.objects.filter(slug=slug, is_active=True, is_published=True).first()
    if item is None: return Response({"detail": "Not found."}, status=404)
    return Response(IndustrySerializer(item, context={"request": request}).data)
