from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        ttl_days = getattr(settings, "AUTH_TOKEN_TTL_DAYS", 30)
        if ttl_days and token.created < timezone.now() - timedelta(days=ttl_days):
            token.delete()
            raise exceptions.AuthenticationFailed("توکن منقضی شده است.")
        return user, token

    def authenticate(self, request):
        header_result = super().authenticate(request)
        if header_result:
            return header_result
        token = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
        if not token:
            return None
        try:
            return self.authenticate_credentials(token)
        except exceptions.AuthenticationFailed:
            # A stale cookie (token deleted server-side via logout, expired,
            # password change/reset, or DB redeploy) must never lock the
            # user out: treat it as "no credentials" so public endpoints
            # such as login/register/otp still run and issue a fresh token.
            return None
