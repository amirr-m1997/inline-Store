from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Case, Count, Exists, F, IntegerField, Max, Min, OuterRef, Q, Value, When

from .models import AttributeDefinition, Category, CategoryAttribute, Product, ProductAttributeValue, ProductBrand
from .search_normalization import normalize_search_text


class CatalogQueryService:
    """Builds a validated, facet-aware catalog queryset without per-product lookups."""

    def __init__(self, queryset, params):
        self.base_queryset = queryset
        self.params = params
        self.category = self._category()
        self.allowed_attributes = self._allowed_attributes()
        self.applied = {"query": self.params.get("q") or None, "category": self.category.id if self.category else None, "brand": [], "availability": None, "price": {}, "attributes": {}}
        self.order_fields = []

    def _csv(self, key):
        return [item.strip() for item in self.params.get(key, "").split(",") if item.strip()]

    def _category(self):
        raw = self.params.get("category")
        if not raw:
            return None
        try:
            return Category.objects.get(pk=int(raw), is_active=True)
        except (Category.DoesNotExist, TypeError, ValueError):
            raise ValidationError({"category": "دسته‌بندی معتبر نیست."})

    def _allowed_attributes(self):
        if self.category:
            category_ids = [self.category.pk]
            ancestor = self.category.parent
            while ancestor:
                category_ids.append(ancestor.pk)
                ancestor = ancestor.parent
            return AttributeDefinition.objects.filter(is_active=True, is_filterable=True, category_settings__category_id__in=category_ids).distinct()
        return AttributeDefinition.objects.filter(is_active=True, is_filterable=True)

    def _attribute_map(self):
        return {attribute.code: attribute for attribute in self.allowed_attributes}

    def _apply_attribute_filter(self, queryset, attribute, values):
        value_qs = ProductAttributeValue.objects.filter(product=OuterRef("pk"), attribute=attribute)
        if attribute.value_type == AttributeDefinition.ValueType.ENUM:
            queryset = queryset.filter(Exists(value_qs.filter(enum_value__in=values)))
        elif attribute.value_type == AttributeDefinition.ValueType.BOOLEAN:
            boolean_values = {value.lower() in ("1", "true", "yes") for value in values}
            queryset = queryset.filter(Exists(value_qs.filter(boolean_value__in=boolean_values)))
        elif attribute.value_type == AttributeDefinition.ValueType.NUMBER:
            try:
                queryset = queryset.filter(Exists(value_qs.filter(number_value__gte=values[0])))
            except (TypeError, ValueError):
                pass
        elif attribute.value_type == AttributeDefinition.ValueType.TEXT and values:
            queryset = queryset.filter(Exists(value_qs.filter(text_value__icontains=values[0])))
        return queryset

    def _apply_search(self, queryset):
        raw_query = self.params.get("q", "").strip()
        normalized = normalize_search_text(raw_query)
        if not normalized:
            return queryset
        arabic_variant = normalized.translate(str.maketrans("یک", "يك"))
        identifier_exact = Q(identifiers__normalized_value=normalized)
        identifier_prefix = Q(identifiers__normalized_value__startswith=normalized)
        exact_code = Q(code__iexact=raw_query) | Q(code__iexact=normalized)
        if connection.vendor == "postgresql":
            from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
            from django.contrib.postgres.search import TrigramSimilarity
            search_query = SearchQuery(normalized, config="simple", search_type="websearch")
            if arabic_variant != normalized:
                search_query |= SearchQuery(arabic_variant, config="simple", search_type="websearch")
            vector = SearchVector("name", weight="A", config="simple") + SearchVector("description", weight="B", config="simple")
            queryset = queryset.annotate(
                catalog_search_rank=Case(When(exact_code, then=Value(1000)), When(identifier_exact, then=Value(950)), When(identifier_prefix, then=Value(800)), default=Value(0), output_field=IntegerField()),
                catalog_text_rank=SearchRank(vector, search_query),
                catalog_trigram_rank=TrigramSimilarity("name", normalized),
            ).filter(Q(catalog_search_rank__gt=0) | Q(catalog_text_rank__gt=0) | Q(catalog_trigram_rank__gte=0.12)).order_by("-catalog_search_rank", "-catalog_text_rank", "-catalog_trigram_rank", "code").distinct()
            return queryset
        search_terms = {raw_query, normalized, arabic_variant}
        text_query = Q()
        for term in search_terms:
            if term:
                text_query |= Q(code__icontains=term) | Q(name__icontains=term) | Q(description__icontains=term) | Q(identifiers__normalized_value__icontains=term)
        return queryset.filter(text_query).annotate(
            catalog_search_rank=Case(When(exact_code, then=Value(1000)), When(identifier_exact, then=Value(950)), When(identifier_prefix, then=Value(800)), default=Value(100), output_field=IntegerField()),
        ).order_by("-catalog_search_rank", "code").distinct()

    def apply(self):
        queryset = self.base_queryset
        queryset = self._apply_search(queryset)
        if self.category:
            queryset = queryset.filter(category_id__in=self.category.descendant_ids())
        brand_values = self._csv("brand")
        if brand_values:
            brand_ids = [int(value) for value in brand_values if value.isdigit()]
            queryset = queryset.filter(brand_id__in=brand_ids)
            self.applied["brand"] = brand_ids
        availability = self.params.get("availability") or self.params.get("in_stock")
        if availability and availability.lower() in ("1", "true", "yes", "in_stock"):
            queryset = queryset.filter(on_hand_quantity__gt=F("reserved_quantity"))
            self.applied["availability"] = "in_stock"
        price_min = self.params.get("price_min")
        price_max = self.params.get("price_max")
        if price_min or price_max:
            if price_min:
                try:
                    queryset = queryset.filter(catalog_price_amount__gte=price_min)
                except (TypeError, ValueError):
                    price_min = None
            if price_max:
                try:
                    queryset = queryset.filter(catalog_price_amount__lte=price_max)
                except (TypeError, ValueError):
                    price_max = None
            self.applied["price"] = {"min": price_min, "max": price_max}
        attribute_map = self._attribute_map()
        for code, attribute in attribute_map.items():
            values = self._csv(f"attr_{code}")
            minimum = self.params.get(f"attr_{code}_min")
            maximum = self.params.get(f"attr_{code}_max")
            if attribute.value_type == AttributeDefinition.ValueType.NUMBER and (minimum or maximum):
                range_qs = ProductAttributeValue.objects.filter(product=OuterRef("pk"), attribute=attribute)
                if minimum:
                    try: range_qs = range_qs.filter(number_value__gte=minimum)
                    except (TypeError, ValueError): minimum = None
                if maximum:
                    try: range_qs = range_qs.filter(number_value__lte=maximum)
                    except (TypeError, ValueError): maximum = None
                queryset = queryset.filter(Exists(range_qs))
                self.applied["attributes"][code] = {"min": minimum, "max": maximum}
            elif values:
                queryset = self._apply_attribute_filter(queryset, attribute, values)
                self.applied["attributes"][code] = values
        requested = self.params.get("sort") or self.params.get("ordering", "code")
        aliases = {"newest": "-created_at", "price": "catalog_price_sort", "availability": "-catalog_availability_sort", "discount": "-discount_percentage", "code": "code", "name": "name"}
        requested = aliases.get(requested, requested)
        if requested.lstrip("-") not in {"code", "name", "created_at", "catalog_price_sort", "catalog_availability_sort", "discount_percentage", "on_hand_quantity"}:
            requested = "code"
        self.order_fields = []
        if self.params.get("q", "").strip():
            self.order_fields.append(("catalog_search_rank", True))
            if connection.vendor == "postgresql":
                self.order_fields.extend((("catalog_text_rank", True), ("catalog_trigram_rank", True)))
        self.order_fields.append((requested.lstrip("-"), requested.startswith("-")))
        self.order_fields.append(("id", False))
        queryset = queryset.order_by(*[f"-{field}" if descending else field for field, descending in self.order_fields])
        return queryset

    def _facet_products(self, queryset):
        return Product.objects.filter(pk__in=queryset.values("pk"))

    def facets(self, queryset):
        facets = []
        price_bounds = queryset.aggregate(min=Min("catalog_price_amount"), max=Max("catalog_price_amount"))
        if price_bounds["min"] is not None or price_bounds["max"] is not None:
            facets.append({"name": "price", "label": "قیمت", "type": "range", "min": price_bounds["min"], "max": price_bounds["max"], "unit": "ریال", "selected": self.applied["price"] or None})
        brand_counts = list(queryset.filter(brand__isnull=False).values("brand_id", "brand__name").annotate(count=Count("pk", distinct=True)).order_by("brand__name"))
        brands = self.applied["brand"]
        if brand_counts:
            facets.append({"name": "brand", "label": "برند", "type": "checkbox", "options": [{"value": str(row["brand_id"]), "label": row["brand__name"], "count": row["count"], "selected": row["brand_id"] in brands} for row in brand_counts]})
        for attribute in self.allowed_attributes:
            value_qs = ProductAttributeValue.objects.filter(product__in=queryset.values("pk"), attribute=attribute)
            selected = self.applied["attributes"].get(attribute.code)
            if attribute.value_type == AttributeDefinition.ValueType.NUMBER:
                bounds = value_qs.aggregate(min=Min("number_value"), max=Max("number_value"))
                if bounds["min"] is not None:
                    facets.append({"name": attribute.code, "label": attribute.name_fa, "type": "range", "min": bounds["min"], "max": bounds["max"], "unit": attribute.unit, "selected": selected})
            elif attribute.value_type in (AttributeDefinition.ValueType.ENUM, AttributeDefinition.ValueType.BOOLEAN):
                field = "enum_value" if attribute.value_type == AttributeDefinition.ValueType.ENUM else "boolean_value"
                counts = value_qs.values(field).annotate(count=Count("product_id", distinct=True)).order_by(field)
                options = [{"value": str(row[field]).lower() if isinstance(row[field], bool) else str(row[field]), "label": str(row[field]), "count": row["count"], "selected": (str(row[field]).lower() if isinstance(row[field], bool) else str(row[field])) in (selected or [])} for row in counts]
                if options:
                    facets.append({"name": attribute.code, "label": attribute.name_fa, "type": "checkbox" if attribute.value_type == AttributeDefinition.ValueType.ENUM else "boolean", "options": options, "selected": selected})
        category_qs = Category.objects.filter(is_active=True, parent_id=self.category.id if self.category else None).annotate(count=Count("products", filter=Q(products__in=self._facet_products(queryset)), distinct=True)).order_by("code")
        category_options = [{"value": str(row.id), "label": row.name_fa, "count": row.count, "selected": self.category is not None and row.id == self.category.id} for row in category_qs if row.count]
        if category_options:
            facets.append({"name": "category", "label": "دسته‌بندی", "type": "hierarchical_category", "options": category_options})
        return facets

    def result(self):
        queryset = self.apply()
        return queryset, {"facets": self.facets(queryset), "applied_filters": self.applied}
