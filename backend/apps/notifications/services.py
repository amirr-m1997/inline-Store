import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import NotificationDelivery
from .sms import UnconfiguredSmsBackend

logger = logging.getLogger("notifications")

EVENTS = NotificationDelivery.EventType
MAX_ERROR_LENGTH = 500


def _safe_error(exc):
    value = " ".join(str(exc).split())
    for secret_name in ("EMAIL_HOST_PASSWORD", "SMS_PASSWORD"):
        secret = str(getattr(settings, secret_name, ""))
        if secret:
            value = value.replace(secret, "[redacted]")
    return value[:MAX_ERROR_LENGTH] or "delivery failed"


def _locale(locale):
    return "en" if locale == "en" else "fa"


def _allowed_channels(*, email, phone, preferred_contact_method):
    preferred = (preferred_contact_method or "").strip().lower()
    channels = []
    if getattr(settings, "NOTIFICATIONS_EMAIL_ENABLED", False) and email:
        try:
            validate_email(email)
        except Exception:
            email = None
        if email and (not preferred or preferred == "email"):
            channels.append((NotificationDelivery.Channel.EMAIL, email.strip().lower()))
    if getattr(settings, "NOTIFICATIONS_SMS_ENABLED", False) and phone:
        if not preferred or preferred in {"sms", "phone"}:
            channels.append((NotificationDelivery.Channel.SMS, phone.strip()))
    return channels


def _subject(event_type, locale, payload):
    if locale == "en":
        return {
            EVENTS.RFQ_SUBMITTED: "Your request for quotation was submitted",
            EVENTS.QUOTATION_ISSUED: f"Quotation {payload.get('quotation_reference', '')} is available",
            EVENTS.QUOTATION_ACCEPTED: "Your quotation response was recorded",
            EVENTS.QUOTATION_REJECTED: "Your quotation response was recorded",
            EVENTS.QUOTATION_REVISION_REQUESTED: "Your quotation revision request was recorded",
        }[event_type]
    return {
        EVENTS.RFQ_SUBMITTED: "ثبت درخواست استعلام قیمت",
        EVENTS.QUOTATION_ISSUED: f"صدور پیشنهاد قیمت {payload.get('quotation_reference', '')}",
        EVENTS.QUOTATION_ACCEPTED: "ثبت پاسخ شما به پیشنهاد قیمت",
        EVENTS.QUOTATION_REJECTED: "ثبت پاسخ شما به پیشنهاد قیمت",
        EVENTS.QUOTATION_REVISION_REQUESTED: "ثبت درخواست اصلاح پیشنهاد قیمت",
    }[event_type]


def _sms_text(event_type, locale, payload):
    ref = payload.get("quotation_reference") or payload.get("reference") or ""
    if locale == "en":
        messages = {
            EVENTS.RFQ_SUBMITTED: f"Your RFQ {ref} was received for review.",
            EVENTS.QUOTATION_ISSUED: f"Quotation {ref} is available in your account.",
            EVENTS.QUOTATION_ACCEPTED: f"Your response to quotation {ref} was recorded.",
            EVENTS.QUOTATION_REJECTED: f"Your response to quotation {ref} was recorded.",
            EVENTS.QUOTATION_REVISION_REQUESTED: f"Your revision request for {ref} was recorded.",
        }
    else:
        messages = {
            EVENTS.RFQ_SUBMITTED: f"درخواست استعلام {ref} برای بررسی ثبت شد.",
            EVENTS.QUOTATION_ISSUED: f"پیشنهاد قیمت {ref} در حساب شما در دسترس است.",
            EVENTS.QUOTATION_ACCEPTED: f"پاسخ شما به پیشنهاد {ref} ثبت شد.",
            EVENTS.QUOTATION_REJECTED: f"پاسخ شما به پیشنهاد {ref} ثبت شد.",
            EVENTS.QUOTATION_REVISION_REQUESTED: f"درخواست اصلاح پیشنهاد {ref} ثبت شد.",
        }
    return messages[event_type]


def _message(delivery):
    payload = delivery.payload or {}
    if delivery.channel == NotificationDelivery.Channel.SMS:
        return _sms_text(delivery.event_type, _locale(delivery.locale), payload)
    template = f"notifications/email/{_locale(delivery.locale)}/"
    if delivery.event_type == EVENTS.RFQ_SUBMITTED:
        name = "rfq_submitted.txt"
    elif delivery.event_type == EVENTS.QUOTATION_ISSUED:
        name = "quotation_issued.txt"
    else:
        name = "quotation_response.txt"
    return render_to_string(template + name, payload).strip()


def get_sms_backend():
    path = getattr(settings, "SMS_BACKEND", "")
    if not path:
        return UnconfiguredSmsBackend()
    return import_string(path)()


def deliver_notification(delivery_id):
    """Deliver one log entry; failures are recorded and never raised to business callers."""
    now = timezone.now()
    with transaction.atomic():
        delivery = NotificationDelivery.objects.select_for_update().filter(pk=delivery_id).first()
        if not delivery or delivery.status == NotificationDelivery.Status.SENT:
            return delivery
        if delivery.attempt_count >= getattr(settings, "NOTIFICATIONS_MAX_ATTEMPTS", 3):
            return delivery
        delivery.attempt_count += 1
        delivery.last_attempt_at = now
        delivery.next_retry_at = None
        delivery.save(update_fields=("attempt_count", "last_attempt_at", "next_retry_at"))
        try:
            if not getattr(settings, "NOTIFICATIONS_REAL_DELIVERY_ENABLED", False):
                raise RuntimeError("real notification delivery is disabled")
            body = _message(delivery)
            if delivery.channel == NotificationDelivery.Channel.EMAIL:
                EmailMultiAlternatives(delivery.subject, body, settings.DEFAULT_FROM_EMAIL, [delivery.recipient]).send(fail_silently=False)
            else:
                get_sms_backend().send_sms(delivery.recipient, body, context={"event_type": delivery.event_type, "reference": delivery.related_reference})
        except Exception as exc:
            delivery.status = NotificationDelivery.Status.FAILED
            delivery.error_code = "delivery_failed"
            delivery.error_message = _safe_error(exc)
            if delivery.attempt_count < getattr(settings, "NOTIFICATIONS_MAX_ATTEMPTS", 3):
                delivery.next_retry_at = now + timedelta(minutes=min(60, 2 ** delivery.attempt_count))
            delivery.save(update_fields=("status", "error_code", "error_message", "next_retry_at"))
            logger.warning("notification delivery failed event=%s channel=%s reference=%s attempt=%s error=%s", delivery.event_type, delivery.channel, delivery.related_reference, delivery.attempt_count, delivery.error_message)
            return delivery
        delivery.status = NotificationDelivery.Status.SENT
        delivery.sent_at = timezone.now()
        delivery.error_code = ""
        delivery.error_message = ""
        delivery.save(update_fields=("status", "sent_at", "error_code", "error_message", "next_retry_at"))
        return delivery


def queue_notification(*, event_type, related_reference, email="", phone="", locale="fa", preferred_contact_method="", payload=None):
    """Create idempotent channel logs and deliver them only after the surrounding commit."""
    locale = _locale(locale)
    payload = dict(payload or {})
    deliveries = []
    for channel, recipient in _allowed_channels(email=email, phone=phone, preferred_contact_method=preferred_contact_method):
        subject = _subject(event_type, locale, payload)
        delivery, created = NotificationDelivery.objects.get_or_create(
            event_type=event_type, channel=channel, recipient=recipient,
            locale=locale, related_reference=related_reference, template_version="v1",
            defaults={"subject": subject, "payload": payload},
        )
        if created:
            transaction.on_commit(lambda delivery_id=delivery.pk: deliver_notification(delivery_id))
        deliveries.append(delivery)
    return deliveries


def _contact(rfq):
    return {"email": rfq.email, "phone": rfq.phone, "preferred_contact_method": rfq.preferred_contact_method}


def notify_rfq_submitted(rfq):
    return queue_notification(event_type=EVENTS.RFQ_SUBMITTED, related_reference=rfq.reference, locale="fa", payload={"reference": rfq.reference, "item_count": rfq.items.count()}, **_contact(rfq))


def notify_quotation_issued(quotation):
    rfq = quotation.rfq
    return queue_notification(
        event_type=EVENTS.QUOTATION_ISSUED, related_reference=quotation.reference, locale="fa",
        payload={"quotation_reference": quotation.reference, "rfq_reference": rfq.reference, "issued_at": quotation.issued_at.strftime("%Y-%m-%d") if quotation.issued_at else "", "expires_at": quotation.expires_at.strftime("%Y-%m-%d") if quotation.expires_at else ""},
        **_contact(rfq),
    )


def notify_quotation_response(quotation, response):
    rfq = quotation.rfq
    labels = {"accepted": ("Accepted", "تأیید شده"), "rejected": ("Rejected", "رد شده"), "revision_requested": ("Revision requested", "درخواست اصلاح")}
    english, persian = labels[response.response]
    return queue_notification(
        event_type=getattr(EVENTS, "QUOTATION_" + response.response.upper()), related_reference=quotation.reference,
        locale="fa", payload={"quotation_reference": quotation.reference, "rfq_reference": rfq.reference, "response_label": persian},
        **_contact(rfq),
    )
