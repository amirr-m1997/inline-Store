from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.notifications.models import NotificationDelivery
from apps.notifications.services import deliver_notification


class Command(BaseCommand):
    help = "Retry bounded failed or pending notification deliveries."

    def add_arguments(self, parser):
        parser.add_argument("--channel", choices=["email", "sms"], default=None)
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        now = timezone.now()
        queryset = NotificationDelivery.objects.filter(
            status__in=(NotificationDelivery.Status.PENDING, NotificationDelivery.Status.FAILED),
            attempt_count__lt=getattr(settings, "NOTIFICATIONS_MAX_ATTEMPTS", 3),
        ).filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=now))
        if options["channel"]:
            queryset = queryset.filter(channel=options["channel"])
        ids = list(queryset.order_by("created_at").values_list("pk", flat=True)[:max(0, options["limit"])])
        for delivery_id in ids:
            deliver_notification(delivery_id)
        self.stdout.write(self.style.SUCCESS(f"Processed {len(ids)} notification deliveries."))
