from django.conf import settings
from rest_framework.authentication import TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        header_result = super().authenticate(request)
        if header_result:
            return header_result
        token = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
        return self.authenticate_credentials(token) if token else None
