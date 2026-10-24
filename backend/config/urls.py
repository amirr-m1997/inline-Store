import os
import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as static_serve
from rest_framework.schemas import get_schema_view

from apps.notifications.config import parse_env_bool

from .api import ApiRootView
from apps.dashboard.admin_views import advanced_admin_index, management_report_export, management_reports_view

# Branded admin console: titles shown in the header/footer of every admin page,
# and "View site" pointing at the storefront instead of the API host.
admin.site.site_header = "پنل مدیریت مهر اصل"
admin.site.site_title = "مهر اصل"
admin.site.index_title = "داشبورد مدیریت"
admin.site.site_url = settings.FRONTEND_URL

schema_view = get_schema_view(title="Company Store API", description="Versioned API foundation", version="1.0.0")
urlpatterns = [
    path("admin/reports/management/", admin.site.admin_view(management_reports_view), name="management-reports"),
    path("admin/reports/management/export.xlsx", admin.site.admin_view(management_report_export), name="management-report-export"),
    path("admin/", admin.site.admin_view(advanced_admin_index), name="admin-index"),
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
# Uploaded files (/media/) used to be served by Django only when DEBUG=True, so on
# production-like hosts (DEBUG=False, no dedicated file mapping in IIS/nginx)
# every product image, logo and document came back 404 and the storefront showed
# broken images. SERVE_MEDIA=True restores Django-side media serving without
# turning DEBUG on (default still follows DEBUG, so local/dev behavior is unchanged).
SERVE_MEDIA = parse_env_bool(os.environ.get("SERVE_MEDIA"), default=settings.DEBUG)
if SERVE_MEDIA:
    # NOTE: django.conf.urls.static.static() silently returns [] when DEBUG=False,
    # so the pattern is built directly to make SERVE_MEDIA work on production hosts.
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
            static_serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
