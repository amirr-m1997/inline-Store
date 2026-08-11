import logging
from django.conf import settings

logger = logging.getLogger("accounts.sms")


def send_otp(phone, code):
    """Development adapter; replace this function with an Iranian SMS provider adapter in production."""
    if settings.DEBUG:
        logger.info("Development OTP for %s: %s", phone[-4:], code)
