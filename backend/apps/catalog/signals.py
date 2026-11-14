import json
import logging
import urllib.request

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Product

logger = logging.getLogger("catalog.signals")


def notify_frontend_revalidate(tag=None, path=None):
    revalidate_url = getattr(settings, "NEXTJS_REVALIDATE_URL", "http://frontend:3000/api/revalidate")
    secret = getattr(settings, "REVALIDATION_SECRET", "mehrasl-cache-secret-2026")
    try:
        data = json.dumps({"tag": tag, "path": path}).encode("utf-8")
        req = urllib.request.Request(
            revalidate_url,
            data=data,
            headers={"Content-Type": "application/json", "x-revalidate-secret": secret},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as exc:
        logger.debug("Next.js revalidation ping skipped or failed: %s", exc)


@receiver([post_save, post_delete], sender=Product)
def product_cache_invalidation(sender, instance, **kwargs):
    notify_frontend_revalidate(tag=f"product:{instance.slug}")
    notify_frontend_revalidate(tag="catalog")


@receiver([post_save, post_delete], sender=Category)
def category_cache_invalidation(sender, instance, **kwargs):
    notify_frontend_revalidate(tag="categories")
    notify_frontend_revalidate(tag="catalog")
