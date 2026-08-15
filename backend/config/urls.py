from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.schemas import get_schema_view
from .api import ApiRootView

schema_view = get_schema_view(title="Company Store API", description="Versioned API foundation", version="1.0.0")
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", ApiRootView.as_view(), name="api-v1-root"),
    # Backward-compatible public catalog paths consumed by the frontend.
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/cart/", include("apps.carts.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/customer/", include("apps.orders.customer_urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/pricing/", include("apps.pricing.urls")),
    path("api/v1/company/", include("apps.company.urls")),
    path("api/v1/content/", include("apps.content.urls")),
    path("api/v1/search/", include("apps.search.urls")),
    path("api/v1/rfq/", include("apps.rfq.urls")),
    path("api/v1/site/", include("apps.company.site_urls")),
    path("api/v1/site/", include("apps.website.urls")),
    path("api/schema/", schema_view, name="openapi-schema"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
