from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Case, CharField, Count, DecimalField, ExpressionWrapper, F, IntegerField, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework import filters, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Category, CategorySlugRedirect, Product, ProductBrand, ProductDocument, ProductImage, SupplyBrand
from .serializers import CatalogProductSerializer, CategoryNavigationSerializer, CategorySerializer, ProductBrandSerializer, ProductDetailSerializer, ProductDocumentResourceSerializer, ProductSummarySerializer, SupplyBrandSerializer
from .services import CatalogQueryService
from .cursor import apply_keyset, decode_cursor, encode_cursor
from apps.pricing.models import ProductPrice


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)
    queryset = Category.objects.filter(is_active=True).select_related("parent").prefetch_related("children")
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("code", "name_fa", "level")
    ordering = ("level", "code")

    @action(detail=False, methods=("get",), pagination_class=None)
    def roots(self, request):
        cache_key = "category_roots_v1"
        data = cache.get(cache_key)
        if data is None:
            roots = Category.objects.filter(is_active=True, parent=None).order_by("code")
            data = CategoryNavigationSerializer(roots, many=True, context={"request": request}).data
            cache.set(cache_key, data, 300)
        return Response(data)

    @action(detail=False, methods=("get",), url_path=r"children/(?P<parent_id>[^/.]+)", pagination_class=None)
    def children(self, request, parent_id=None):
        cache_key = f"category_children_v1_{parent_id}"
        data = cache.get(cache_key)
        if data is None:
            children = Category.objects.filter(is_active=True, parent_id=parent_id).order_by("code")
            data = CategoryNavigationSerializer(children, many=True, context={"request": request}).data
            cache.set(cache_key, data, 300)
        return Response(data)

    @action(detail=False, methods=("get",), url_path=r"by-slug/(?P<slug>[^/.]+)", pagination_class=None)
    def by_slug(self, request, slug=None):
        category = Category.objects.filter(is_active=True, slug=slug).first()
        if not category:
            legacy = CategorySlugRedirect.objects.select_related("category").filter(
                old_slug=slug, category__is_active=True,
            ).first()
            if not legacy:
                return Response({"detail": "Not found."}, status=404)
            data = dict(CategoryNavigationSerializer(legacy.category, context={"request": request}).data)
            data["redirect_slug"] = legacy.category.slug
            return Response(data)
        return Response(CategoryNavigationSerializer(category, context={"request": request}).data)

    @action(detail=False, methods=("get",), pagination_class=None)
    def tree(self, request):
        """Return the complete category tree and product counts in one bounded query."""
        cache_key = "category_tree_v1"
        roots = cache.get(cache_key)
        if roots is None:
            categories = list(Category.objects.filter(is_active=True).annotate(product_count=Count("products", filter=Q(products__is_active=True))).order_by("parent_id", "code"))
            nodes = {category.id: {"id": category.id, "code": category.code, "name_fa": category.name_fa, "name_en": category.name_en, "slug": category.slug, "level": category.level, "product_count": category.product_count, "children": []} for category in categories}
            roots = []
            for category in categories:
                node = nodes[category.id]
                if category.parent_id and category.parent_id in nodes:
                    nodes[category.parent_id]["children"].append(node)
                else:
                    roots.append(node)
            def accumulate(node):
                node["product_count"] += sum(accumulate(child) for child in node["children"])
                return node["product_count"]
            for root in roots:
                accumulate(root)
            cache.set(cache_key, roots, 300)
        return Response(roots)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CatalogProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("code", "name", "unit")
    ordering_fields = ("code", "name", "created_at", "on_hand_quantity", "reserved_quantity", "discount_percentage")
    ordering = ("code",)

    def get_serializer_class(self):
        if self.action in ("retrieve", "by_slug"):
            return ProductDetailSerializer
        return CatalogProductSerializer

    def get_queryset(self):
        now = timezone.now()
        current_prices = ProductPrice.objects.filter(
            product=OuterRef("pk"), effective_from__lte=now,
        ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=now)).order_by("-effective_from")
        primary_image = ProductImage.objects.filter(product=OuterRef("pk")).order_by(
            Case(When(is_primary=True, then=Value(0)), default=Value(1), output_field=IntegerField()), "sort_order", "id",
        )
        queryset = Product.objects.filter(is_active=True).select_related("category", "inventory", "brand")
        queryset = queryset.annotate(
            on_hand_quantity=F("inventory__on_hand_quantity"),
            reserved_quantity=F("inventory__reserved_quantity"),
            discount_percentage=Coalesce(Subquery(current_prices.values("discount_percentage")[:1], output_field=DecimalField(max_digits=5, decimal_places=2)), Value(0), output_field=DecimalField(max_digits=5, decimal_places=2)),
            catalog_price_amount=Subquery(current_prices.values("amount")[:1], output_field=DecimalField(max_digits=18, decimal_places=2)),
            catalog_price_currency=Subquery(current_prices.values("currency")[:1], output_field=CharField()),
            catalog_image_id=Subquery(primary_image.values("id")[:1]),
            catalog_image_name=Subquery(primary_image.values("image")[:1], output_field=CharField()),
            catalog_image_alt_text=Subquery(primary_image.values("alt_text")[:1], output_field=CharField()),
            catalog_image_alt_fa=Subquery(primary_image.values("alt_fa")[:1], output_field=CharField()),
            catalog_image_alt_en=Subquery(primary_image.values("alt_en")[:1], output_field=CharField()),
            catalog_image_is_primary=Subquery(primary_image.values("is_primary")[:1]),
            catalog_image_sort_order=Subquery(primary_image.values("sort_order")[:1]),
        )
        queryset = queryset.annotate(
            catalog_price_sort=Coalesce(F("catalog_price_amount"), Value(0), output_field=DecimalField(max_digits=18, decimal_places=2)),
            catalog_availability_sort=ExpressionWrapper(
                Coalesce(F("on_hand_quantity"), Value(0), output_field=DecimalField(max_digits=18, decimal_places=6))
                - Coalesce(F("reserved_quantity"), Value(0), output_field=DecimalField(max_digits=18, decimal_places=6)),
                output_field=DecimalField(max_digits=18, decimal_places=6),
            ),
        )
        if self.action not in ("list", "catalog_query"):
            queryset = queryset.prefetch_related("images", "documents")
        category = self.request.query_params.get("category")
        if category:
            try:
                root = Category.objects.get(pk=category, is_active=True)
            except (Category.DoesNotExist, ValueError):
                return queryset.none()
            queryset = queryset.filter(category_id__in=root.descendant_ids())
        if self.request.query_params.get("in_stock", "").lower() in ("1", "true", "yes"):
            queryset = queryset.filter(on_hand_quantity__gt=F("reserved_quantity"))
        if self.request.query_params.get("discounted", "").lower() in ("1", "true", "yes"):
            queryset = queryset.filter(discount_percentage__gt=0)
        if self.request.query_params.get("featured", "").lower() in ("1", "true", "yes"):
            queryset = queryset.filter(is_featured=True)
        return queryset

    @action(detail=False, methods=("get",), url_path="catalog-query")
    def catalog_query(self, request):
        """Explicit faceted-query contract; the legacy list endpoint is unchanged."""
        try:
            service = CatalogQueryService(self.get_queryset(), request.query_params)
            queryset, metadata = service.result()
        except ValidationError as error:
            return Response({"detail": error.message_dict}, status=400)
        cursor_mode = "cursor" in request.query_params or "page" not in request.query_params
        if cursor_mode:
            if "page" in request.query_params:
                return Response({"detail": {"pagination": "page and cursor modes cannot be combined."}}, status=400)
            try:
                page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
            except (TypeError, ValueError):
                return Response({"detail": {"page_size": "page_size must be an integer."}}, status=400)
            full_queryset = queryset
            try:
                if request.query_params.get("cursor"):
                    cursor_fields = decode_cursor(request.query_params["cursor"], request.query_params, service.order_fields)
                    queryset = apply_keyset(queryset, cursor_fields)
            except ValidationError as error:
                return Response({"detail": error.message_dict}, status=400)
            rows = list(queryset[: page_size + 1])
            has_more = len(rows) > page_size
            products = rows[:page_size]
            next_cursor = encode_cursor(request.query_params, service.order_fields, products[-1]) if has_more and products else None
            return Response({
                "products": CatalogProductSerializer(products, many=True, context={"request": request}).data,
                "total_count": full_queryset.count(),
                "next_cursor": next_cursor,
                "previous_cursor": None,
                "has_more": has_more,
                "facets": metadata["facets"],
                "applied_filters": metadata["applied_filters"],
            })
        page = self.paginate_queryset(queryset)
        products = page if page is not None else queryset
        payload = {
            "products": CatalogProductSerializer(products, many=True, context={"request": request}).data,
            "total_count": queryset.count(),
            "facets": metadata["facets"],
            "applied_filters": metadata["applied_filters"],
            "page": getattr(self.paginator, "page", None).number if page is not None else None,
            "next_cursor": None,
        }
        if page is not None:
            payload["next"] = self.paginator.get_next_link()
            payload["previous"] = self.paginator.get_previous_link()
        return Response(payload)

    def retrieve(self, request, pk=None):
        lookup = Q(slug=pk)
        if str(pk).isdigit():
            lookup |= Q(pk=int(pk))
        product = self.get_queryset().filter(lookup).first()
        if not product:
            return Response({"detail": "Not found."}, status=404)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)

    @action(detail=False, methods=("get",), url_path=r"by-slug/(?P<slug>[^/.]+)")
    def by_slug(self, request, slug=None):
        product = self.get_queryset().filter(slug=slug).first()
        if not product:
            return Response({"detail": "Not found."}, status=404)
        return Response(ProductDetailSerializer(product, context={"request": request}).data)

    @action(detail=True, methods=("get",), url_path="discovery")
    def discovery(self, request, pk=None):
        from apps.content.discovery import product_discovery
        from apps.content.serializers import ContentArticleListSerializer, FAQEntrySerializer
        product = self.get_queryset().filter(Q(slug=pk) | Q(pk=int(pk) if str(pk).isdigit() else -1)).first()
        if not product:
            return Response({"detail": "Not found."}, status=404)
        result = product_discovery(product)
        context = {"request": request}
        return Response({
            "articles": ContentArticleListSerializer(result["articles"], many=True, context=context).data,
            "faqs": FAQEntrySerializer(result["faqs"], many=True, context=context).data,
            "resources": ProductDocumentResourceSerializer(result["resources"], many=True, context=context).data,
            "products": ProductSummarySerializer(result["products"], many=True, context=context).data,
        })


class SupplyBrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplyBrandSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = SupplyBrand.objects.filter(is_active=True).order_by("order", "name")


class ProductBrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductBrandSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    lookup_field = "slug"
    queryset = ProductBrand.objects.filter(is_active=True, is_published=True, products__is_active=True).exclude(slug__isnull=True).exclude(slug="").distinct().order_by("name")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["brief"] = self.action == "retrieve"
        return context


@api_view(["GET"])
@permission_classes([AllowAny])
def product_documents(request):
    documents = ProductDocument.objects.filter(product__is_active=True, is_active=True, is_published=True).select_related("product", "product__category", "product__brand")
    document_type = request.query_params.get("document_type") or request.query_params.get("type")
    if document_type:
        documents = documents.filter(document_type=document_type)
    product = request.query_params.get("product")
    if product:
        documents = documents.filter(Q(product__slug=product) | Q(product__code=product))
    category = request.query_params.get("category")
    if category:
        documents = documents.filter(product__category__slug=category)
    brand = request.query_params.get("brand")
    if brand:
        documents = documents.filter(product__brand__slug=brand)
    language = request.query_params.get("language")
    if language:
        documents = documents.filter(language__icontains=language)
    query = (request.query_params.get("q") or "").strip()
    if query:
        documents = documents.filter(
            Q(title_fa__icontains=query) | Q(title_en__icontains=query) | Q(display_name__icontains=query)
            | Q(product__name__icontains=query) | Q(product__code__icontains=query)
        )
    documents = documents.order_by("document_type", "display_order", "id")
    if request.query_params.get("page") or request.query_params.get("page_size"):
        try:
            page_number = max(1, int(request.query_params.get("page", "1")))
        except ValueError:
            page_number = 1
        try:
            page_size = min(50, max(1, int(request.query_params.get("page_size", "24"))))
        except ValueError:
            page_size = 24
        paginator = Paginator(documents, page_size)
        page = paginator.get_page(page_number)
        serializer = ProductDocumentResourceSerializer(page.object_list, many=True, context={"request": request})
        return Response({
            "count": paginator.count,
            "next": page.has_next(),
            "previous": page.has_previous(),
            "results": serializer.data,
        })
    serializer = ProductDocumentResourceSerializer(documents[:100], many=True, context={"request": request})
    return Response(serializer.data)
