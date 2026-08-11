from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


def verify_google_credential(credential):
    if not settings.GOOGLE_CLIENT_ID:
        raise AuthenticationFailed("ورود با گوگل پیکربندی نشده است.")
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
        payload = id_token.verify_oauth2_token(credential, requests.Request(), settings.GOOGLE_CLIENT_ID)
    except Exception as error:
        raise AuthenticationFailed("اعتبار گوگل نامعتبر است.") from error
    if not payload.get("email_verified"):
        raise AuthenticationFailed("ایمیل گوگل تأیید نشده است.")
    return payload
