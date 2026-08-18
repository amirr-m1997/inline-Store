"""CSRF defense for cookie-based API authentication.

DRF only enforces CSRF for SessionAuthentication. The project's
CookieTokenAuthentication reads the auth token from a cookie, so
state-changing requests were protected solely by the cookie's SameSite
flag. This middleware adds the standard Origin/Referer check: when an
unsafe request carries the auth cookie and a foreign Origin/Referer, it
is rejected. Requests without an Origin/Referer (curl, mobile clients)
are unaffected because they cannot be tricked into CSRF by a browser.
"""

from urllib.parse import urlparse

from django.conf import settings
from django.http import JsonResponse

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class CookieAuthOriginCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in UNSAFE_METHODS and settings.AUTH_COOKIE_NAME in request.COOKIES:
            allowed_hosts = {request.get_host()}
            for origin in settings.CSRF_TRUSTED_ORIGINS:
                netloc = urlparse(origin).netloc
                if netloc:
                    allowed_hosts.add(netloc)
            source = request.headers.get("Origin") or request.headers.get("Referer")
            if source:
                netloc = urlparse(source).netloc
                if netloc and netloc not in allowed_hosts:
                    return JsonResponse({"detail": "درخواست از منبع نامعتبر مسدود شد."}, status=403)
        return self.get_response(request)
