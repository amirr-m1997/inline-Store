from rest_framework.response import Response
from rest_framework.views import APIView


class ApiRootView(APIView):
    """Versioned API discovery endpoint owned by the project configuration."""

    def get(self, request):
        return Response({
            "version": "v1",
            "status": "ok",
            "resources": {
                "categories": "/api/v1/categories/",
                "products": "/api/v1/products/",
                "company": "/api/v1/company/",
                "dashboard": "/api/v1/dashboard/",
                "currency_rates": "/api/v1/pricing/currency-rates/",
                "stock": "/api/v1/inventory/stock/",
                "cart": "/api/v1/cart/",
            },
        })
