from celery import shared_task
from django.core.cache import cache

from .api import DASHBOARD_CACHE_KEY, DASHBOARD_CACHE_TTL
from .services import build_dashboard_payload


@shared_task
def refresh_dashboard_cache():
    payload = build_dashboard_payload()
    cache.set(DASHBOARD_CACHE_KEY, payload, DASHBOARD_CACHE_TTL)
    return DASHBOARD_CACHE_KEY