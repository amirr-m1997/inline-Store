from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def notification_configuration_check(app_configs, **kwargs):
    errors = []
    if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        errors.append(Error("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.", id="notifications.E001"))
    if not getattr(settings, "NOTIFICATIONS_REAL_DELIVERY_ENABLED", False):
        return errors
    if getattr(settings, "NOTIFICATIONS_EMAIL_ENABLED", False):
        if not settings.DEFAULT_FROM_EMAIL or not settings.EMAIL_HOST:
            errors.append(Error("Enabled email notifications require DEFAULT_FROM_EMAIL and EMAIL_HOST.", id="notifications.E002"))
        if settings.EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
            errors.append(Warning("Real email delivery is enabled with a non-SMTP backend.", id="notifications.W001"))
    if getattr(settings, "NOTIFICATIONS_SMS_ENABLED", False):
        missing = [name for name in ("SMS_USERNAME", "SMS_PASSWORD", "SMS_PORTAL", "SMS_BACKEND") if not getattr(settings, name, "")]
        if missing:
            errors.append(Error(f"Enabled SMS notifications require configured provider settings: {', '.join(missing)}.", id="notifications.E003"))
    return errors
