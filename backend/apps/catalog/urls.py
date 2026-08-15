from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import CategoryViewSet, ProductBrandViewSet, ProductViewSet, SupplyBrandViewSet, product_documents

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("supply-brands", SupplyBrandViewSet, basename="supply-brand")
router.register("brands", ProductBrandViewSet, basename="product-brand")

urlpatterns = [path("", include(router.urls)), path("documents/", product_documents, name="product-documents")]
