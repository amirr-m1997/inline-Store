from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import CurrencyRateViewSet, ProductPriceViewSet

router = DefaultRouter()
router.register("currency-rates", CurrencyRateViewSet, basename="currency-rate")
router.register("product-prices", ProductPriceViewSet, basename="product-price")

urlpatterns = [path("", include(router.urls))]