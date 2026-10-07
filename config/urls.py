"""مسیرهای اصلی پروژه."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from core import views as core_views


def home(request):
    """مسیر قدیمی «/» به فروشگاه منتقل شد؛ برای سازگاری به سایت مشتری هدایت می‌شود."""
    return redirect("shop:home")


urlpatterns = [
    # سایت مشتری (فروشگاه B2B) — صفحهٔ اصلی و همهٔ مسیرهای خرید/پرداخت
    path("", include("shop.urls")),
    # مسیرهای سفارشی پنل (پیش از admin تا اولویت داشته باشند)
    path("admin/reports/", admin.site.admin_view(core_views.report_view), name="panel-reports"),
    path("admin/reports/export.xlsx", admin.site.admin_view(core_views.report_export_xlsx), name="panel-report-export"),
    path("admin/quick-order/", admin.site.admin_view(core_views.quick_order_view), name="panel-quick-order"),
    path("admin/alerts/", admin.site.admin_view(core_views.alerts_view), name="panel-alerts"),
    path("admin/api/summary/", admin.site.admin_view(core_views.api_summary), name="panel-api-summary"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
