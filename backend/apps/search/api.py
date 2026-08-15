from django.db.models import Case, Count, IntegerField, Prefetch, Q, When
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Category, Product, ProductBrand, ProductImage
from apps.catalog.services import CatalogQueryService
from apps.catalog.search_normalization import normalize_search_text
from apps.content.api import PublicEditorialQuerySetMixin
from apps.company.models import Capability, Industry
from apps.content.models import ContentArticle, FAQEntry
from apps.content.serializers import ContentArticleListSerializer, FAQEntrySerializer


MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 120
GROUP_LIMIT = 8


def _compact(value):
    return " ".join((value or "").split())


def _localized(value_fa, value_en, language):
    return (value_en or value_fa) if language == "en" else (value_fa or value_en)


def _product_payload(product):
    image = next(iter(getattr(product, "_search_images", [])), None)
    return {
        "id": product.id,
        "slug": product.slug,
        "code": product.code,
        "name": product.name,
        "name_fa": product.name,
        "name_en": product.name,
        "unit": product.unit,
        "image": image.image.url if image and image.image else None,
        "category": {"id": product.category_id, "slug": product.category.slug, "name_fa": product.category.name_fa, "name_en": product.category.name_en} if product.category and product.category.is_active else None,
        "brand": {"id": product.brand_id, "slug": product.brand.slug, "name": product.brand.name} if product.brand and product.brand.is_active and product.brand.is_published and product.brand.slug else None,
    }


def _category_payload(category, language):
    return {"id": category.id, "slug": category.slug, "name": _localized(category.name_fa, category.name_en, language), "name_fa": category.name_fa, "name_en": category.name_en, "image": None, "product_count": category.product_count}


def _brand_payload(brand):
    return {"id": brand.id, "slug": brand.slug, "name": brand.name, "logo": brand.logo.url if brand.logo else None, "product_count": brand.product_count}


def _faq_queryset():
    return FAQEntry.objects.filter(is_active=True, is_published=True).prefetch_related(
        Prefetch("products", queryset=Product.objects.filter(is_active=True).only("id", "code", "name", "slug"), to_attr="_faq_products"),
        Prefetch("categories", queryset=Category.objects.filter(is_active=True).only("id", "code", "name_fa", "name_en", "slug"), to_attr="_faq_categories"),
        Prefetch("industries", queryset=Industry.objects.filter(is_active=True, is_published=True).only("id", "slug", "name_fa", "name_en"), to_attr="_faq_industries"),
        Prefetch("capabilities", queryset=Capability.objects.filter(is_active=True, is_published=True).only("id", "slug", "title_fa", "title_en"), to_attr="_faq_capabilities"),
        Prefetch("articles", queryset=ContentArticle.objects.filter(is_active=True, is_published=True, published_at__isnull=False, published_at__lte=timezone.now()).only("id", "slug", "title_fa", "title_en", "content_type"), to_attr="_faq_articles"),
    )


class SearchEditorialQuerySet(PublicEditorialQuerySetMixin):
    pass


@api_view(["GET"])
@permission_classes([AllowAny])
def unified_search(request):
    raw_query = request.query_params.get("q", "")
    query = _compact(raw_query)
    if len(query) > MAX_QUERY_LENGTH:
        return Response({"detail": {"q": f"Search query must be at most {MAX_QUERY_LENGTH} characters."}}, status=400)
    normalized = normalize_search_text(query)
    if len(normalized) < MIN_QUERY_LENGTH:
        return Response({"query": query, "products": [], "categories": [], "brands": [], "articles": [], "faqs": [], "counts": {"products": 0, "categories": 0, "brands": 0, "articles": 0, "faqs": 0}})

    language = "en" if request.query_params.get("lang", "fa").lower().startswith("en") else "fa"
    image_queryset = ProductImage.objects.filter(is_primary=True).only("id", "image", "product_id")
    # Keep product matching aligned with the catalog's proven normalization,
    # identifier handling, ranking, and deduplication rules.
    products_queryset = CatalogQueryService(Product.objects.filter(is_active=True), {"q": raw_query}).apply().select_related("category", "brand").prefetch_related(Prefetch("images", queryset=image_queryset, to_attr="_search_images"))
    products = list(products_queryset[:GROUP_LIMIT])

    categories_queryset = Category.objects.filter(is_active=True).filter(Q(name_fa__icontains=query) | Q(name_en__icontains=query) | Q(slug__icontains=normalized) | Q(code__icontains=normalized)).annotate(product_count=Count("products", filter=Q(products__is_active=True))).order_by("level", "name_fa", "id")
    categories = list(categories_queryset[:GROUP_LIMIT])

    brands_queryset = ProductBrand.objects.filter(is_active=True, is_published=True, products__is_active=True).filter(Q(name__icontains=query) | Q(code__icontains=normalized) | Q(slug__icontains=normalized)).annotate(product_count=Count("products", filter=Q(products__is_active=True))).distinct().order_by("name", "id")
    brands = list(brands_queryset[:GROUP_LIMIT])

    articles_queryset = SearchEditorialQuerySet()._article_queryset().filter(
        Q(title_fa__icontains=query) | Q(title_en__icontains=query) | Q(excerpt_fa__icontains=query) | Q(excerpt_en__icontains=query) | Q(body_fa__icontains=query) | Q(body_en__icontains=query)
    ).distinct().order_by("-published_at", "-id")
    articles = list(articles_queryset.annotate(_demo_rank=Case(When(migration_notes__icontains="demo-content:", then=1), default=0, output_field=IntegerField())).order_by("_demo_rank", "-published_at", "-id")[:GROUP_LIMIT])
    article_data = ContentArticleListSerializer(articles, many=True, context={"request": request}).data
    faqs_queryset = _faq_queryset().filter(
        Q(question_fa__icontains=query) | Q(question_en__icontains=query) | Q(answer_fa__icontains=query) | Q(answer_en__icontains=query)
    ).distinct().order_by("display_order", "id")
    faqs = list(faqs_queryset.annotate(_demo_rank=Case(When(migration_notes__icontains="demo-content:", then=1), default=0, output_field=IntegerField())).order_by("_demo_rank", "display_order", "id")[:GROUP_LIMIT])
    faq_data = FAQEntrySerializer(faqs, many=True, context={"request": request}).data
    return Response({
        "query": query,
        "products": [_product_payload(product) for product in products],
        "categories": [_category_payload(category, language) for category in categories],
        "brands": [_brand_payload(brand) for brand in brands],
        "articles": article_data,
        "faqs": faq_data,
        "counts": {"products": len(products), "categories": len(categories), "brands": len(brands), "articles": len(articles), "faqs": len(faqs)},
    })
