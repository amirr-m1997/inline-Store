from decimal import Decimal

import bleach
from django.db.models import Q
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from rest_framework import serializers

from apps.inventory.models import Issue, Receipt
from apps.pricing.models import ProductPrice
from apps.company.models import CompanyAdvantage

from .models import Category, Product, ProductBrand, ProductDocument, ProductImage, SupplyBrand


def rich_text_to_html(value):
    """Sanitize admin-authored rich text into a safe HTML fragment for public rendering."""
    if not value:
        return value
    return bleach.clean(
        value,
        tags={"p", "div", "br", "span", "strong", "b", "em", "i", "u", "s", "sub", "sup", "ul", "ol", "li", "blockquote", "h2", "h3", "h4", "pre", "hr", "a", "img", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption"},
        attributes={"a": ["href", "title", "target", "rel"], "img": ["src", "alt", "title", "width", "height"], "th": ["colspan", "rowspan", "scope"], "td": ["colspan", "rowspan"], "span": ["class"], "p": ["class"], "div": ["class"]},
        strip=True,
    )


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "code", "name_fa", "name_en", "slug", "parent", "level", "is_active", "children")
        read_only_fields = ("level",)

    def get_children(self, obj):
        # Shallow on purpose: deep trees are served by the dedicated `tree`
        # action (single bounded query). Recursing here caused N+1 queries and
        # unbounded payloads on large catalogs.
        children = obj.children.filter(is_active=True)
        return CategoryNavigationSerializer(children, many=True, context=self.context).data


class CategoryNavigationSerializer(serializers.ModelSerializer):
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "code", "name_fa", "name_en", "slug", "parent", "level", "has_children")

    def get_has_children(self, obj):
        return obj.children.filter(is_active=True).exists()


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    ordering = serializers.IntegerField(source="sort_order", read_only=True)

    class Meta:
        model = ProductImage
        fields = ("id", "url", "image", "alt_text", "alt_fa", "alt_en", "is_primary", "ordering", "sort_order")

    def get_url(self, obj):
        return obj.image.url if obj.image else None

    def get_image(self, obj):
        return self.get_url(obj)


class SupplyBrandSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SupplyBrand
        fields = ("id", "name", "logo", "website")

    def get_logo(self, obj):
        return obj.logo.url if obj.logo else None


class ProductBrandSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = ProductBrand
        fields = ("id", "name", "code", "slug", "logo", "description_fa", "description_en", "website", "product_count", "products", "seo_title_fa", "seo_title_en", "seo_description_fa", "seo_description_en")

    def get_logo(self, obj):
        return obj.logo.url if obj.logo else None

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def get_products(self, obj):
        if self.context.get("brief"):
            return list(obj.products.filter(is_active=True).values("id", "name", "code", "slug")[:24])
        return []


class ProductDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    type = serializers.CharField(source="document_type", read_only=True)
    size = serializers.IntegerField(source="file_size", read_only=True)

    class Meta:
        model = ProductDocument
        fields = ("id", "title", "title_fa", "title_en", "type", "file_url", "file_name", "display_name", "mime_type", "size", "revision", "language")

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_file_name(self, obj):
        return obj.display_name or obj.file.name.rsplit("/", 1)[-1]

    def get_title(self, obj):
        return obj.title_fa or obj.title_en or self.get_file_name(obj)


class ProductDocumentResourceSerializer(ProductDocumentSerializer):
    product = serializers.SerializerMethodField()

    class Meta(ProductDocumentSerializer.Meta):
        fields = ProductDocumentSerializer.Meta.fields + ("product",)

    def get_product(self, obj):
        return {"id": obj.product_id, "name": obj.product.name, "code": obj.product.code, "slug": obj.product.slug}


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    available_quantity = serializers.SerializerMethodField()
    on_hand_quantity = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True, allow_null=True)
    reserved_quantity = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True, allow_null=True)
    name_fa = serializers.CharField(source="name", read_only=True)
    name_en = serializers.SerializerMethodField()
    category_tree = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "code", "name", "name_fa", "name_en", "slug", "category", "category_tree", "unit", "description", "technical_specs", "is_active", "images", "on_hand_quantity", "reserved_quantity", "available_quantity", "price", "brand", "created_at", "updated_at")

    def get_description(self, obj):
        return rich_text_to_html(obj.description)

    def get_brand(self, obj):
        brand = getattr(obj, "brand", None)
        if not brand or not brand.is_active or not brand.is_published or not brand.slug:
            return None
        return {"name": brand.name, "slug": brand.slug}

    def get_available_quantity(self, obj):
        try:
            return obj.inventory.available_quantity
        except obj._meta.get_field("inventory").related_model.DoesNotExist:
            return None

    def get_name_en(self, obj):
        return ""

    def get_category_tree(self, obj):
        nodes, category = [], obj.category
        while category:
            nodes.append({"id": category.id, "name_fa": category.name_fa, "slug": category.slug})
            category = category.parent
        return list(reversed(nodes))

    def get_price(self, obj):
        # Bulk path: cart/checkout/export call sites preload one price map for
        # all items (context["price_map"]) instead of one query per product.
        price_map = (self.context or {}).get("price_map")
        if price_map is not None:
            return price_map.get(obj.pk)
        now = timezone.now()
        price = ProductPrice.objects.filter(product=obj, effective_from__lte=now).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=now)).order_by("-effective_from").first()
        if not price:
            return None
        final = price.amount * (Decimal("1") - price.discount_percentage / Decimal("100"))
        return {"original_amount": str(price.amount), "currency": price.currency, "discount_percentage": str(price.discount_percentage), "final_amount": str(final.quantize(Decimal("0.01")))}


class CatalogCategorySerializer(serializers.ModelSerializer):
    """The category shape needed by catalog cards, without recursive children."""
    class Meta:
        model = Category
        fields = ("id", "code", "name_fa", "name_en", "slug", "parent", "level", "is_active")


class CatalogProductSerializer(serializers.ModelSerializer):
    """Small public listing serializer backed entirely by list-query annotations."""
    category = CatalogCategorySerializer(read_only=True)
    name_fa = serializers.CharField(source="name", read_only=True)
    name_en = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()
    on_hand_quantity = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True, allow_null=True)
    reserved_quantity = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True, allow_null=True)
    price = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "code", "name", "name_fa", "name_en", "slug", "category", "unit", "images", "on_hand_quantity", "reserved_quantity", "available_quantity", "price", "brand", "short_description", "created_at", "updated_at")

    def get_short_description(self, obj):
        text = strip_tags(obj.description or "")
        text = " ".join(text.split())
        return Truncator(text).chars(160) if text else ""

    def get_brand(self, obj):
        brand = getattr(obj, "brand", None)
        if not brand or not brand.is_active or not brand.is_published or not brand.slug:
            return None
        return {"name": brand.name, "slug": brand.slug}

    def get_name_en(self, obj):
        return ""

    def get_available_quantity(self, obj):
        if obj.on_hand_quantity is None or obj.reserved_quantity is None:
            return None
        return obj.on_hand_quantity - obj.reserved_quantity

    def get_images(self, obj):
        image_name = getattr(obj, "catalog_image_name", None)
        if not image_name:
            return []
        storage = ProductImage._meta.get_field("image").storage
        return [{
            "id": obj.catalog_image_id,
            "url": storage.url(image_name),
            "image": storage.url(image_name),
            "alt_text": obj.catalog_image_alt_text or "",
            "alt_fa": obj.catalog_image_alt_fa or "",
            "alt_en": obj.catalog_image_alt_en or "",
            "is_primary": bool(obj.catalog_image_is_primary),
            "ordering": obj.catalog_image_sort_order or 0,
            "sort_order": obj.catalog_image_sort_order or 0,
        }]

    def get_price(self, obj):
        if obj.catalog_price_amount is None:
            return None
        discount = obj.discount_percentage or Decimal("0")
        final = obj.catalog_price_amount * (Decimal("1") - discount / Decimal("100"))
        return {"original_amount": str(obj.catalog_price_amount), "currency": obj.catalog_price_currency, "discount_percentage": str(discount), "final_amount": str(final.quantize(Decimal("0.01")))}


class ProductDetailSerializer(ProductSerializer):
    sku = serializers.CharField(source="code", read_only=True)
    inventory = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    technical_specifications = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    service_advantages = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + (
            "sku", "inventory", "pricing", "technical_specifications", "related_products", "service_advantages", "documents",
        )

    def get_inventory(self, obj):
        inventory = getattr(obj, "inventory", None)
        last_receipt = Receipt.objects.filter(product=obj).order_by("-occurred_at").values_list("occurred_at", flat=True).first()
        last_issue = Issue.objects.filter(product=obj).order_by("-occurred_at").values_list("occurred_at", flat=True).first()
        return {
            "available": inventory.on_hand_quantity if inventory else None,
            "reserved": inventory.reserved_quantity if inventory else None,
            "net": inventory.available_quantity if inventory else None,
            "allowed_for_cart": inventory.available_quantity if inventory else 0,
            "last_receipt_date": last_receipt,
            "last_issue_date": last_issue,
        }

    def get_pricing(self, obj):
        # Public storefront price only. Purchase cost (last_purchase_irr,
        # receipt rates) is back-office data and must never leak to anonymous
        # clients — it discloses margins.
        selling = self.get_price(obj)
        return {
            "price": selling["original_amount"] if selling else None,
            "currency": selling["currency"] if selling else None,
            "discount_percentage": selling["discount_percentage"] if selling else None,
            "final_price": selling["final_amount"] if selling else None,
        }

    def get_technical_specifications(self, obj):
        specs = obj.technical_specs or {}
        return [{"label": str(label), "value": value} for label, value in specs.items()]

    def get_related_products(self, obj):
        products = Product.objects.filter(is_active=True, category=obj.category).exclude(pk=obj.pk).prefetch_related("images")[:4]
        return ProductSummarySerializer(products, many=True, context=self.context).data

    def get_service_advantages(self, obj):
        return list(CompanyAdvantage.objects.filter(is_active=True).values(
            "id", "title_fa", "title_en", "description_fa", "description_en", "icon",
        )[:3])

    def get_documents(self, obj):
        documents = obj.documents.filter(is_active=True, is_published=True)
        return ProductDocumentSerializer(documents, many=True, context=self.context).data


class ProductSummarySerializer(serializers.ModelSerializer):
    name_fa = serializers.CharField(source="name", read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "slug", "code", "name_fa", "unit", "primary_image")

    def get_primary_image(self, obj):
        image = next((item for item in obj.images.all() if item.is_primary), None)
        image = image or next(iter(obj.images.all()), None)
        if not image:
            return None
        return image.image.url
