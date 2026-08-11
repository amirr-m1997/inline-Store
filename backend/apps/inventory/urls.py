from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import IssueViewSet, ReceiptViewSet, StockViewSet

router = DefaultRouter()
router.register("stock", StockViewSet, basename="stock")
router.register("receipts", ReceiptViewSet, basename="receipt")
router.register("issues", IssueViewSet, basename="issue")

urlpatterns = [path("", include(router.urls))]