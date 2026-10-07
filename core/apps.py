from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "هسته و لاگ حسابرسی"

    def ready(self):
        from . import signals  # noqa: F401
        from .audit import track_all

        track_all()
