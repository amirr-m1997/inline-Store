from rest_framework import serializers

from .models import ContentArticle, ContentCategory, FAQEntry


def _image_url(value, request):
    if not value:
        return None
    return request.build_absolute_uri(value.url) if request else value.url


class ContentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCategory
        fields = ("id", "slug", "name_fa", "name_en", "description_fa", "description_en", "display_order")


class ContentArticleSerializer(serializers.ModelSerializer):
    content_type_label = serializers.CharField(source="get_content_type_display", read_only=True)
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    related_catalog_categories = serializers.SerializerMethodField()
    related_brands = serializers.SerializerMethodField()
    related_industries = serializers.SerializerMethodField()
    related_capabilities = serializers.SerializerMethodField()

    class Meta:
        model = ContentArticle
        fields = (
            "id", "slug", "content_type", "content_type_label", "title", "title_fa", "title_en",
            "excerpt", "excerpt_fa", "excerpt_en", "featured_image", "published_at", "is_featured",
            "category", "related_products", "related_catalog_categories", "related_brands",
            "related_industries", "related_capabilities", "body", "body_fa", "body_en",
            "seo_title", "seo_title_fa", "seo_title_en", "seo_description", "seo_description_fa",
            "seo_description_en", "author",
        )

    def _language(self):
        language = self.context.get("request").query_params.get("lang", "fa") if self.context.get("request") else "fa"
        return "en" if language.lower().startswith("en") else "fa"

    def _localized(self, obj, field):
        language = self._language()
        value = getattr(obj, f"{field}_{language}")
        return value or getattr(obj, f"{field}_fa") or getattr(obj, f"{field}_en")

    def get_title(self, obj): return self._localized(obj, "title")
    def get_excerpt(self, obj): return self._localized(obj, "excerpt")
    def get_body(self, obj): return self._localized(obj, "body")
    def get_seo_title(self, obj): return self._localized(obj, "seo_title")
    def get_seo_description(self, obj): return self._localized(obj, "seo_description")

    def get_featured_image(self, obj):
        return _image_url(obj.featured_image, self.context.get("request"))

    def get_category(self, obj):
        category = obj.category
        return ContentCategorySerializer(category, context=self.context).data if category else None

    @staticmethod
    def _values(items, fields):
        return [{key: getattr(item, key) for key in fields} for item in items]

    @staticmethod
    def _relation(obj, attr, manager_name):
        value = getattr(obj, attr, None)
        return value if value is not None else getattr(obj, manager_name).all()

    def get_related_products(self, obj):
        return self._values(self._relation(obj, "_content_products", "products"), ("id", "code", "name", "slug"))

    def get_related_catalog_categories(self, obj):
        return self._values(self._relation(obj, "_content_catalog_categories", "catalog_categories"), ("id", "code", "name_fa", "name_en", "slug"))

    def get_related_brands(self, obj):
        return self._values(self._relation(obj, "_content_brands", "brands"), ("id", "name", "slug"))

    def get_related_industries(self, obj):
        return self._values(self._relation(obj, "_content_industries", "industries"), ("id", "slug", "name_fa", "name_en"))

    def get_related_capabilities(self, obj):
        return self._values(self._relation(obj, "_content_capabilities", "capabilities"), ("id", "slug", "title_fa", "title_en"))


class ContentArticleListSerializer(ContentArticleSerializer):
    class Meta(ContentArticleSerializer.Meta):
        fields = (
            "id", "slug", "content_type", "content_type_label", "title", "title_fa", "title_en",
            "excerpt", "excerpt_fa", "excerpt_en", "featured_image", "published_at", "is_featured",
            "category", "related_products", "related_catalog_categories", "related_brands",
            "related_industries", "related_capabilities",
        )


class FAQEntrySerializer(serializers.ModelSerializer):
    faq_type_label = serializers.CharField(source="get_faq_type_display", read_only=True)
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    related_categories = serializers.SerializerMethodField()
    related_industries = serializers.SerializerMethodField()
    related_capabilities = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()

    class Meta:
        model = FAQEntry
        fields = (
            "id", "slug", "faq_type", "faq_type_label", "question", "question_fa", "question_en",
            "answer", "answer_fa", "answer_en", "display_order", "related_products", "related_categories",
            "related_industries", "related_capabilities", "related_articles",
        )

    def _language(self):
        request = self.context.get("request")
        language = request.query_params.get("lang", "fa") if request else "fa"
        return "en" if language.lower().startswith("en") else "fa"

    def _localized(self, obj, field):
        language = self._language()
        preferred = getattr(obj, f"{field}_{language}")
        return preferred or getattr(obj, f"{field}_fa") or getattr(obj, f"{field}_en")

    def get_question(self, obj): return self._localized(obj, "question")
    def get_answer(self, obj): return self._localized(obj, "answer")

    @staticmethod
    def _values(items, fields):
        return [{key: getattr(item, key) for key in fields} for item in items]

    @staticmethod
    def _relation(obj, attr, manager_name):
        value = getattr(obj, attr, None)
        return value if value is not None else getattr(obj, manager_name).all()

    def get_related_products(self, obj):
        return self._values(self._relation(obj, "_faq_products", "products"), ("id", "code", "name", "slug"))

    def get_related_categories(self, obj):
        return self._values(self._relation(obj, "_faq_categories", "categories"), ("id", "code", "name_fa", "name_en", "slug"))

    def get_related_industries(self, obj):
        return self._values(self._relation(obj, "_faq_industries", "industries"), ("id", "slug", "name_fa", "name_en"))

    def get_related_capabilities(self, obj):
        return self._values(self._relation(obj, "_faq_capabilities", "capabilities"), ("id", "slug", "title_fa", "title_en"))

    def get_related_articles(self, obj):
        return self._values(self._relation(obj, "_faq_articles", "articles"), ("id", "slug", "title_fa", "title_en", "content_type"))
