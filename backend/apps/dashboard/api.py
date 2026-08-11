from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import build_dashboard_payload

DASHBOARD_CACHE_KEY = "dashboard_summary_v1"
DASHBOARD_CACHE_TTL = 60


@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_summary(request):
    payload = cache.get(DASHBOARD_CACHE_KEY)
    if payload is None:
        payload = build_dashboard_payload()
        cache.set(DASHBOARD_CACHE_KEY, payload, DASHBOARD_CACHE_TTL)
    return Response(payload)