from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import ContentArticleViewSet, ContentCategoryViewSet, FAQEntryViewSet

router = DefaultRouter()
router.register("articles", ContentArticleViewSet, basename="content-article")
router.register("faqs", FAQEntryViewSet, basename="content-faq")
router.register("categories", ContentCategoryViewSet, basename="content-category")

urlpatterns = [path("", include(router.urls))]
