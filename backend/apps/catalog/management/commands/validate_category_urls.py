from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIRequestFactory

from apps.catalog.api import CategoryViewSet
from apps.catalog.models import Category, CategorySlugRedirect


class Command(BaseCommand):
    help = "Validate that every active category slug resolves through the public detail action."

    def handle(self, *args, **options):
        categories = list(Category.objects.filter(is_active=True).only("id", "slug"))
        slugs = [category.slug for category in categories]
        if any(not slug for slug in slugs):
            raise CommandError("An active category has an empty slug.")
        if len(slugs) != len(set(slugs)):
            raise CommandError("Active category slugs are not globally unique.")

        factory = APIRequestFactory()
        view = CategoryViewSet.as_view({"get": "by_slug"})
        failures = []
        for category in categories:
            response = view(factory.get(f"/api/v1/categories/by-slug/{category.slug}/"), slug=category.slug)
            if response.status_code != 200 or response.data.get("id") != category.id:
                failures.append(category.slug)

        redirects = list(CategorySlugRedirect.objects.select_related("category"))
        for redirect in redirects:
            response = view(factory.get(f"/api/v1/categories/by-slug/{redirect.old_slug}/"), slug=redirect.old_slug)
            if response.status_code != 200 or response.data.get("redirect_slug") != redirect.category.slug:
                failures.append(redirect.old_slug)

        if failures:
            raise CommandError(f"Unresolvable category slugs: {', '.join(failures[:20])}")
        self.stdout.write(self.style.SUCCESS(
            f"Validated {len(categories)} canonical and {len(redirects)} legacy category URLs; failures=0"
        ))
