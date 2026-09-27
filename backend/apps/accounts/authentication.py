from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
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
            # A stale cookie (token deleted server-side via logout,
            # password change/reset, or DB redeploy) must never lock the
            # user out: treat it as "no credentials" so public endpoints
            # such as login/register/otp still run and issue a fresh token.
            return None
