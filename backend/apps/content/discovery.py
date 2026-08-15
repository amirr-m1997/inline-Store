"""Deterministic, publication-aware discovery queries for public content."""

from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from apps.catalog.models import Product, ProductDocument
from .models import ContentArticle, FAQEntry


DEFAULT_LIMITS = {"articles": 4, "faqs": 5, "resources": 5, "products": 4}


def _demo_rank(field="migration_notes"):
    return Case(
        When(**{f"{field}__icontains": "demo-content:"}, then=Value(1)),
        default=Value(0),
        output_field=IntegerField(),
    )


def public_articles():
    now = timezone.now()
    return ContentArticle.objects.filter(
        is_active=True, is_published=True, published_at__isnull=False, published_at__lte=now,
    ).select_related("category").prefetch_related("products", "catalog_categories", "brands", "industries", "capabilities")


def public_faqs():
    return FAQEntry.objects.filter(is_active=True, is_published=True).prefetch_related("products", "categories", "industries", "capabilities", "articles")


def public_resources():
    return ProductDocument.objects.filter(
        product__is_active=True, is_active=True, is_published=True,
    ).select_related("product", "product__category", "product__brand")


def _article_order(queryset, limit, priority=None):
    ordering = ["_demo_rank", "-is_featured", "display_order", "-published_at", "-id"]
    if priority:
        ordering.insert(0, priority)
    return queryset.annotate(_demo_rank=_demo_rank()).distinct().order_by(*ordering)[:limit]


def _faq_order(queryset, limit):
    return queryset.annotate(_demo_rank=_demo_rank()).distinct().order_by(
        "_demo_rank", "display_order", "id",
    )[:limit]


def product_discovery(product, limits=None):
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    article_query = Q(products=product) | Q(catalog_categories=product.category)
    articles = public_articles().filter(article_query).annotate(
        _relationship_rank=Case(
            When(products=product, then=Value(50)),
            When(catalog_categories=product.category, then=Value(40)),
            default=Value(0), output_field=IntegerField(),
        ),
    )
    articles = _article_order(articles, limits["articles"], "-_relationship_rank")
    faq_query = Q(products=product) | Q(categories=product.category)
    faqs = _faq_order(public_faqs().filter(faq_query), limits["faqs"])
    resources = public_resources().filter(product=product).order_by("document_type", "display_order", "id")[:limits["resources"]]
    products = Product.objects.filter(is_active=True, category=product.category).exclude(pk=product.pk).prefetch_related("images").order_by("name", "id")[:limits["products"]]
    return {"articles": articles, "faqs": faqs, "resources": resources, "products": products}


def article_discovery(article, limits=None):
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    product_ids = list(article.products.values_list("id", flat=True))
    category_ids = list(article.catalog_categories.values_list("id", flat=True))
    brand_ids = list(article.brands.values_list("id", flat=True))
    industry_ids = list(article.industries.values_list("id", flat=True))
    capability_ids = list(article.capabilities.values_list("id", flat=True))
    relation_query = Q(products__in=product_ids) | Q(catalog_categories__in=category_ids) | Q(brands__in=brand_ids) | Q(industries__in=industry_ids) | Q(capabilities__in=capability_ids)
    related_articles = public_articles().filter(relation_query).exclude(pk=article.pk)
    related_articles = related_articles.annotate(
        _relationship_rank=Case(
            When(products__in=product_ids, then=Value(50)),
            When(catalog_categories__in=category_ids, then=Value(40)),
            When(brands__in=brand_ids, then=Value(30)),
            When(industries__in=industry_ids, then=Value(20)),
            When(capabilities__in=capability_ids, then=Value(10)),
            default=Value(0), output_field=IntegerField(),
        ),
    )
    related_articles = _article_order(related_articles, limits["articles"], "-_relationship_rank")
    faq_query = Q(articles=article) | Q(products__in=product_ids) | Q(categories__in=category_ids) | Q(industries__in=industry_ids) | Q(capabilities__in=capability_ids)
    faqs = _faq_order(public_faqs().filter(faq_query), limits["faqs"])
    resources_query = Q(product__content_articles=article)
    if category_ids:
        resources_query |= Q(product__category__in=category_ids)
    resources = public_resources().filter(resources_query).order_by("document_type", "display_order", "id")[:limits["resources"]]
    products = Product.objects.none()
    if not product_ids and category_ids:
        products = Product.objects.filter(is_active=True, category__in=category_ids).prefetch_related("images").order_by("name", "id")[:limits["products"]]
    return {"articles": related_articles, "faqs": faqs, "resources": resources, "products": products}
