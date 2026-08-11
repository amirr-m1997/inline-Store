from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import CategoryViewSet, ProductViewSet, SupplyBrandViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("supply-brands", SupplyBrandViewSet, basename="supply-brand")

urlpatterns = [path("", include(router.urls))]
