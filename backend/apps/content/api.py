from django.db.models import Case, IntegerField, Prefetch, Q, When
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Category, Product, ProductBrand
from apps.company.models import Capability, Industry
from .models import ContentArticle, ContentCategory, FAQEntry
from .serializers import ContentArticleListSerializer, ContentArticleSerializer, ContentCategorySerializer, FAQEntrySerializer
from .discovery import article_discovery
from rest_framework.decorators import action


class PublicEditorialQuerySetMixin:
    def _public(self, queryset):
        return queryset.filter(is_active=True, is_published=True, published_at__isnull=False, published_at__lte=timezone.now())

    def _article_queryset(self):
        public_products = Product.objects.filter(is_active=True).only("id", "code", "name", "slug")
        public_categories = Category.objects.filter(is_active=True).only("id", "code", "name_fa", "name_en", "slug")
        public_brands = ProductBrand.objects.filter(is_active=True, is_published=True).only("id", "name", "slug")
        public_industries = Industry.objects.filter(is_active=True, is_published=True).only("id", "slug", "name_fa", "name_en")
        public_capabilities = Capability.objects.filter(is_active=True, is_published=True).only("id", "slug", "title_fa", "title_en")
        return self._public(ContentArticle.objects.select_related("category", "author").prefetch_related(
            Prefetch("products", queryset=public_products, to_attr="_content_products"),
            Prefetch("catalog_categories", queryset=public_categories, to_attr="_content_catalog_categories"),
            Prefetch("brands", queryset=public_brands, to_attr="_content_brands"),
            Prefetch("industries", queryset=public_industries, to_attr="_content_industries"),
            Prefetch("capabilities", queryset=public_capabilities, to_attr="_content_capabilities"),
        ))


class ContentCategoryViewSet(PublicEditorialQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentCategorySerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    lookup_field = "slug"

    def get_queryset(self):
        return ContentCategory.objects.filter(is_active=True, is_published=True).order_by("display_order", "name_fa", "id")


class ContentArticleViewSet(PublicEditorialQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ContentArticleSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("published_at", "display_order", "title_fa")
    ordering = ("display_order", "-published_at", "-id")

    def get_serializer_class(self):
        return ContentArticleSerializer if self.action == "retrieve" else ContentArticleListSerializer

    def get_queryset(self):
        queryset = self._article_queryset()
        params = self.request.query_params
        if params.get("content_type"):
            queryset = queryset.filter(content_type=params["content_type"])
        if params.get("category"):
            queryset = queryset.filter(category__slug=params["category"], category__is_active=True, category__is_published=True)
        if params.get("product"):
            value = params["product"]
            queryset = queryset.filter(Q(products__slug=value) | Q(products__code=value))
        if params.get("catalog_category"):
            value = params["catalog_category"]
            category_lookup = Q(catalog_categories__slug=value)
            if value.isdigit():
                category_lookup |= Q(catalog_categories__id=int(value))
            queryset = queryset.filter(category_lookup)
        if params.get("brand"):
            queryset = queryset.filter(brands__slug=params["brand"])
        if params.get("industry"):
            queryset = queryset.filter(industries__slug=params["industry"])
        if params.get("capability"):
            queryset = queryset.filter(capabilities__slug=params["capability"])
        if params.get("featured", "").lower() in ("1", "true", "yes"):
            queryset = queryset.filter(is_featured=True)
        return queryset.annotate(_demo_rank=Case(When(migration_notes__icontains="demo-content:", then=1), default=0, output_field=IntegerField())).distinct().order_by("_demo_rank", "display_order", "-published_at", "-id")

    @action(detail=True, methods=("get",), url_path="discovery")
    def discovery(self, request, slug=None):
        article = self.get_queryset().filter(slug=slug).first()
        if article is None:
            return Response({"detail": "Not found."}, status=404)
        from apps.catalog.serializers import ProductDocumentResourceSerializer, ProductSummarySerializer
        from .serializers import ContentArticleListSerializer, FAQEntrySerializer
        result = article_discovery(article)
        context = {"request": request}
        return Response({
            "articles": ContentArticleListSerializer(result["articles"], many=True, context=context).data,
            "faqs": FAQEntrySerializer(result["faqs"], many=True, context=context).data,
            "resources": ProductDocumentResourceSerializer(result["resources"], many=True, context=context).data,
            "products": ProductSummarySerializer(result["products"], many=True, context=context).data,
        })


class FAQEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FAQEntrySerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    lookup_field = "slug"

    def get_queryset(self):
        public = lambda model: model.objects.filter(is_active=True)
        queryset = FAQEntry.objects.filter(is_active=True, is_published=True).prefetch_related(
            Prefetch("products", queryset=public(Product).only("id", "code", "name", "slug"), to_attr="_faq_products"),
            Prefetch("categories", queryset=public(Category).only("id", "code", "name_fa", "name_en", "slug"), to_attr="_faq_categories"),
            Prefetch("industries", queryset=Industry.objects.filter(is_active=True, is_published=True).only("id", "slug", "name_fa", "name_en"), to_attr="_faq_industries"),
            Prefetch("capabilities", queryset=Capability.objects.filter(is_active=True, is_published=True).only("id", "slug", "title_fa", "title_en"), to_attr="_faq_capabilities"),
            Prefetch("articles", queryset=ContentArticle.objects.filter(is_active=True, is_published=True, published_at__isnull=False, published_at__lte=timezone.now()).only("id", "slug", "title_fa", "title_en", "content_type"), to_attr="_faq_articles"),
        )
        params = self.request.query_params
        if params.get("type"):
            queryset = queryset.filter(faq_type=params["type"])
        if params.get("product"):
            queryset = queryset.filter(Q(products__slug=params["product"]) | Q(products__code=params["product"]))
        if params.get("category"):
            queryset = queryset.filter(categories__slug=params["category"])
        if params.get("industry"):
            queryset = queryset.filter(industries__slug=params["industry"])
        if params.get("capability"):
            queryset = queryset.filter(capabilities__slug=params["capability"])
        if params.get("article"):
            article_lookup = Q(articles__slug=params["article"])
            if params["article"].isdigit():
                article_lookup |= Q(articles__id=int(params["article"]))
            queryset = queryset.filter(article_lookup)
        return queryset.annotate(_demo_rank=Case(When(migration_notes__icontains="demo-content:", then=1), default=0, output_field=IntegerField())).distinct().order_by("_demo_rank", "display_order", "id")
