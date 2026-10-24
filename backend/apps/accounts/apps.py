from django.apps import AppConfig
from django.db.models.signals import post_migrate


def initialize_internal_roles(**kwargs):
    from .roles import ensure_internal_roles
    ensure_internal_roles()


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        # Keeps fresh deployments in sync after `migrate`; existing deployments
        # are also reconciled by the explicit setup_internal_roles command.
        post_migrate.connect(
            initialize_internal_roles,
            sender=self,
            dispatch_uid="accounts.ensure_internal_roles",
            weak=False,
        )

