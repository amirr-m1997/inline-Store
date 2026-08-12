from django.core.cache import cache
from django.db.models import Count, DecimalField, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Category, CategorySlugRedirect, Product, SupplyBrand
from .serializers import CategoryNavigationSerializer, CategorySerializer, ProductDetailSerializer, ProductSerializer, SupplyBrandSerializer
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
            categories = list(Category.objects.filter(is_active=True).annotate(product_count=Count("products")).order_by("parent_id", "code"))
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
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("code", "name", "unit")
    ordering_fields = ("code", "name", "created_at", "on_hand_quantity", "reserved_quantity", "discount_percentage")
    ordering = ("code",)

    def get_queryset(self):
        now = timezone.now()
        current_discount = ProductPrice.objects.filter(
            product=OuterRef("pk"), effective_from__lte=now,
        ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=now)).order_by("-effective_from").values("discount_percentage")[:1]
        queryset = Product.objects.filter(is_active=True).select_related("category", "inventory").prefetch_related("images")
        queryset = queryset.annotate(
            on_hand_quantity=F("inventory__on_hand_quantity"),
            reserved_quantity=F("inventory__reserved_quantity"),
            discount_percentage=Coalesce(Subquery(current_discount, output_field=DecimalField()), Value(0), output_field=DecimalField()),
        )
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


class SupplyBrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplyBrandSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = SupplyBrand.objects.filter(is_active=True).order_by("order", "name")
