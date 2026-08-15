from django.db import models


class NotificationDelivery(models.Model):
    class EventType(models.TextChoices):
        RFQ_SUBMITTED = "rfq_submitted", "RFQ submitted"
        QUOTATION_ISSUED = "quotation_issued", "Quotation issued"
        QUOTATION_ACCEPTED = "quotation_accepted", "Quotation accepted"
        QUOTATION_REJECTED = "quotation_rejected", "Quotation rejected"
        QUOTATION_REVISION_REQUESTED = "quotation_revision_requested", "Quotation revision requested"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    event_type = models.CharField(max_length=48, choices=EventType.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    recipient = models.CharField(max_length=254)
    locale = models.CharField(max_length=8, default="fa")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    subject = models.CharField(max_length=255, blank=True)
    related_reference = models.CharField(max_length=64, blank=True)
    template_version = models.CharField(max_length=16, default="v1")
    payload = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [models.UniqueConstraint(
            fields=("event_type", "channel", "recipient", "related_reference", "template_version"),
            name="notification_event_delivery_unique",
        )]
        indexes = [
            models.Index(fields=("status", "next_retry_at"), name="notif_status_retry_idx"),
            models.Index(fields=("related_reference", "created_at"), name="notif_reference_created_idx"),
        ]
        verbose_name = "تحویل اعلان"
        verbose_name_plural = "تحویل اعلان‌ها"

    def __str__(self):
        return f"{self.event_type} / {self.channel} / {self.related_reference or '-'}"
