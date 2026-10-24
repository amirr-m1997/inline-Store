import json

from .audit import reset_request, set_request
from .textnorm import normalize_json_data


class AuditContextMiddleware:
    """کاربر و مسیر درخواست را برای signalهای audit در دسترس می‌گذارد."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = set_request(request)
        try:
            return self.get_response(request)
        finally:
            reset_request(token)


class PersianDisplayMiddleware:
    """Arabic keyboard variants (ي/ك/...) must never reach the browser.

    Normalizes every string of outgoing JSON API responses to Persian forms,
    so database text typed on Arabic keyboards displays correctly everywhere
    (storefront, search results, documents). Non-JSON responses
    (HTML admin, files, PDFs) pass through untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")
        if not content_type.startswith("application/json"):
            return response
        if getattr(response, "streaming", False):
            return response
        try:
            data = json.loads(response.content.decode(response.charset or "utf-8"))
        except (ValueError, UnicodeDecodeError, LookupError):
            return response
        normalized = normalize_json_data(data)
        response.content = json.dumps(normalized, ensure_ascii=False).encode("utf-8")
        if response.has_header("Content-Length"):
            response.headers["Content-Length"] = str(len(response.content))
        return response
