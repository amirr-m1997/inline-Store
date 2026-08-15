from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.notifications.models import NotificationDelivery
from apps.notifications.services import queue_notification


class Command(BaseCommand):
    help = "Explicitly test configured notification delivery to an operator-supplied recipient."

    def add_arguments(self, parser):
        parser.add_argument("--email")
        parser.add_argument("--sms")
        parser.add_argument("--confirm", action="store_true", help="Required safety acknowledgement for real delivery.")

    def handle(self, *args, **options):
        email, phone = options.get("email"), options.get("sms")
        if bool(email) == bool(phone):
            raise CommandError("Provide exactly one of --email or --sms.")
        if not options["confirm"] or not settings.NOTIFICATIONS_REAL_DELIVERY_ENABLED:
            raise CommandError("Real delivery is disabled or --confirm was not supplied.")
        channel = NotificationDelivery.Channel.EMAIL if email else NotificationDelivery.Channel.SMS
        deliveries = queue_notification(
            event_type=NotificationDelivery.EventType.RFQ_SUBMITTED,
            related_reference="SMOKE-OPERATOR",
            email=email or "", phone=phone or "",
            payload={"reference": "SMOKE-OPERATOR", "item_count": 0},
        )
        if not deliveries or deliveries[0].channel != channel:
            raise CommandError("The requested channel is not enabled or the recipient is invalid.")
        self.stdout.write(self.style.SUCCESS("Notification smoke delivery was attempted; inspect the private delivery log."))
