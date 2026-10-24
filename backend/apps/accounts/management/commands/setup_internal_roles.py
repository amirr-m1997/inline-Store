from django.core.management.base import BaseCommand

from apps.accounts.roles import ensure_internal_roles


class Command(BaseCommand):
    help = "Create or update the predefined internal administration roles."

    def handle(self, *args, **options):
        results = ensure_internal_roles()
        self.stdout.write(self.style.SUCCESS(f"Configured {len(results)} internal role groups."))
