"""سیگنال‌ها: ثبت رخدادهای ورود/خروج و فعال‌سازی ردیابی خودکار مدل‌ها."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .audit import log, track_all
from .models import AuditLog


@receiver(user_login_failed, dispatch_uid="audit_login_failed")
def on_login_failed(sender, credentials, request=None, **kwargs):
    username = (credentials or {}).get("username", "?")
    log(
        action=AuditLog.Action.LOGIN_FAILED,
        model_name="auth.user",
        object_id="",
        object_repr=f"تلاش ورود ناموفق: {username}",
        note=f"نام کاربری: {username}",
        request=request,
    )


@receiver(user_logged_in, dispatch_uid="audit_login")
def on_login(sender, request, user, **kwargs):
    log(
        action=AuditLog.Action.LOGIN,
        model_name="auth.user",
        object_id=str(user.pk),
        object_repr=f"ورود {user.get_username()}",
        actor=user,
        request=request,
    )


@receiver(user_logged_out, dispatch_uid="audit_logout")
def on_logout(sender, request, user, **kwargs):
    if user is not None:
        log(
            action=AuditLog.Action.LOGOUT,
            model_name="auth.user",
            object_id=str(user.pk),
            object_repr=f"خروج {user.get_username()}",
            actor=user,
            request=request,
        )


@receiver(post_migrate, dispatch_uid="audit_track_all")
def on_post_migrate(sender, **kwargs):
    if sender.name in ("catalog", "customers"):
        track_all()


def ready():
    track_all()
