from datetime import timedelta
from unittest.mock import Mock, patch
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.notifications.config import parse_env_bool
from apps.notifications.models import NotificationDelivery
from apps.notifications.services import (
    EVENTS,
    deliver_notification,
    notify_quotation_issued,
    notify_quotation_response,
    notify_rfq_submitted,
    queue_notification,
)
from apps.rfq.models import RequestForQuotation, RequestForQuotationItem, SalesQuotation, SalesQuotationItem, SalesQuotationResponse


class FakeSmsBackend:
    sent = []

    def send_sms(self, recipient, message, *, context=None):
        self.sent.append((recipient, message))


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="notification-user", password="x", email="buyer@example.test")
        category = Category.objects.create(code="NOTIF-CAT", name_fa="دسته اعلان", slug="notification-category")
        self.product = Product.objects.create(code="NOTIF-PRODUCT", name="Notification product", slug="notification-product", category=category, unit="عدد", is_active=True)
        self.rfq = RequestForQuotation.objects.create(customer=self.user, contact_name="Buyer", phone="09121234567", email="buyer@example.test", message="Need review")
        self.rfq_item = RequestForQuotationItem.objects.create(rfq=self.rfq, product=self.product, requested_quantity=2, product_code_snapshot=self.product.code, product_name_snapshot=self.product.name)
        self.client = APIClient()

    def notify(self, callback, *args):
        with self.captureOnCommitCallbacks(execute=True):
            return callback(*args)

    def make_quote(self, issued=True):
        quote = SalesQuotation.objects.create(rfq=self.rfq, status=SalesQuotation.Status.ISSUED if issued else SalesQuotation.Status.DRAFT, currency=SalesQuotation.Currency.IRR)
        SalesQuotationItem.objects.create(quotation=quote, source_rfq_item=self.rfq_item, product=self.product, product_name_snapshot=self.product.name, product_code_snapshot=self.product.code, quantity=2, unit_price="12.50")
        return quote

    def test_boolean_parser_is_not_truthy_for_false(self):
        self.assertFalse(parse_env_bool("False"))
        self.assertFalse(parse_env_bool("0"))
        self.assertTrue(parse_env_bool("yes"))

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_rfq_submitted_email_is_sent_and_idempotent(self):
        self.notify(notify_rfq_submitted, self.rfq)
        self.notify(notify_rfq_submitted, self.rfq)
        self.assertEqual(NotificationDelivery.objects.filter(event_type=EVENTS.RFQ_SUBMITTED).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.rfq.reference, mail.outbox[0].body)

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_rfq_api_hook_queues_after_commit(self):
        self.client.force_authenticate(self.user)
        payload = {"contact_name": "Buyer", "phone": "09121234567", "email": "buyer@example.test", "message": "API event", "items": [{"product": self.product.pk, "requested_quantity": 1}]}
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/v1/rfq/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(NotificationDelivery.objects.filter(event_type=EVENTS.RFQ_SUBMITTED, related_reference=response.json()["reference"], status=NotificationDelivery.Status.SENT).exists())

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_quotation_issued_and_response_events_are_logged(self):
        quote = self.make_quote()
        self.notify(notify_quotation_issued, quote)
        response = SalesQuotationResponse.objects.create(quotation=quote, customer=self.user, response=SalesQuotationResponse.ResponseType.ACCEPTED)
        self.notify(notify_quotation_response, quote, response)
        self.assertEqual(NotificationDelivery.objects.filter(related_reference=quote.reference).count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_all_customer_response_event_types_have_distinct_idempotent_logs(self):
        quote = self.make_quote()
        for response_type in ("accepted", "rejected", "revision_requested"):
            response = SimpleNamespace(response=response_type)
            self.notify(notify_quotation_response, quote, response)
        self.assertEqual(set(NotificationDelivery.objects.filter(related_reference=quote.reference).values_list("event_type", flat=True)), {
            EVENTS.QUOTATION_ACCEPTED, EVENTS.QUOTATION_REJECTED, EVENTS.QUOTATION_REVISION_REQUESTED,
        })

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_SMS_ENABLED=True, SMS_BACKEND="tests.test_notifications.FakeSmsBackend")
    def test_sms_uses_adapter_and_never_guesses_provider_transport(self):
        FakeSmsBackend.sent = []
        self.notify(notify_rfq_submitted, self.rfq)
        self.assertEqual(len(FakeSmsBackend.sent), 1)
        self.assertIn(self.rfq.reference, FakeSmsBackend.sent[0][1])

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_email_failure_is_logged_without_raising(self):
        with patch("apps.notifications.services.EmailMultiAlternatives") as message_class:
            message_class.return_value.send.side_effect = RuntimeError("SMTP connection refused")
            self.notify(notify_rfq_submitted, self.rfq)
        delivery = NotificationDelivery.objects.get(event_type=EVENTS.RFQ_SUBMITTED)
        self.assertEqual(delivery.status, NotificationDelivery.Status.FAILED)
        self.assertIn("SMTP connection refused", delivery.error_message)
        self.rfq.refresh_from_db()
        self.assertEqual(self.rfq.status, RequestForQuotation.Status.SUBMITTED)

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_rollback_removes_log_and_sends_nothing(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                queue_notification(event_type=EVENTS.RFQ_SUBMITTED, related_reference="ROLLBACK", email="buyer@example.test", payload={"reference": "ROLLBACK", "item_count": 1})
                raise RuntimeError("rollback")
        self.assertFalse(NotificationDelivery.objects.filter(related_reference="ROLLBACK").exists())
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=True, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.test")
    def test_retry_sends_failed_delivery_but_not_sent_twice_or_past_limit(self):
        delivery = NotificationDelivery.objects.create(event_type=EVENTS.RFQ_SUBMITTED, channel="email", recipient="retry@example.test", locale="en", subject="Retry", related_reference="RETRY", payload={"reference": "RETRY", "item_count": 1}, status="failed", attempt_count=1, next_retry_at=timezone.now() - timedelta(minutes=1))
        call_command("retry_notifications", stdout=None)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, NotificationDelivery.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)
        deliver_notification(delivery.pk)
        self.assertEqual(len(mail.outbox), 1)
        exhausted = NotificationDelivery.objects.create(event_type=EVENTS.QUOTATION_ISSUED, channel="email", recipient="exhausted@example.test", locale="en", subject="Exhausted", related_reference="EXHAUSTED", payload={}, status="failed", attempt_count=3, next_retry_at=timezone.now() - timedelta(minutes=1))
        call_command("retry_notifications", stdout=None)
        exhausted.refresh_from_db()
        self.assertEqual(exhausted.attempt_count, 3)

    def test_admin_changelist_is_available_without_public_api(self):
        admin_user = get_user_model().objects.create_superuser(username="notif-admin", email="admin@example.test", password="x")
        self.client.login(username="notif-admin", password="x")
        NotificationDelivery.objects.create(event_type=EVENTS.RFQ_SUBMITTED, channel="email", recipient="buyer@example.test", related_reference=self.rfq.reference, payload={})
        self.assertEqual(self.client.get("/admin/notifications/notificationdelivery/").status_code, 200)

    @override_settings(NOTIFICATIONS_REAL_DELIVERY_ENABLED=False, NOTIFICATIONS_EMAIL_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
    def test_disabled_real_delivery_never_contacts_smtp(self):
        with patch("apps.notifications.services.EmailMultiAlternatives") as message_class:
            self.notify(notify_rfq_submitted, self.rfq)
            message_class.assert_not_called()
        self.assertEqual(NotificationDelivery.objects.get(event_type=EVENTS.RFQ_SUBMITTED).status, NotificationDelivery.Status.FAILED)
