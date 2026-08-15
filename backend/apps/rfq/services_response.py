from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import RequestForQuotation, SalesQuotation, SalesQuotationResponse


class QuotationResponseError(ValidationError):
    """A customer response cannot be recorded in the current state."""

    def __init__(self, message, *, not_found=False):
        self.not_found = not_found
        super().__init__(message)


@transaction.atomic
def record_customer_response(*, reference, customer, response, note=""):
    quotation = (
        SalesQuotation.objects.select_for_update()
        .select_related("rfq")
        .filter(reference=reference)
        .first()
    )
    if not quotation or quotation.rfq.customer_id != customer.pk:
        raise QuotationResponseError("پیشنهاد قیمت یافت نشد.", not_found=True)
    if quotation.status != SalesQuotation.Status.ISSUED:
        raise QuotationResponseError("این پیشنهاد در حال حاضر قابل پاسخ نیست.")
    if quotation.expires_at and quotation.expires_at <= timezone.now():
        raise QuotationResponseError("مهلت پاسخ به این پیشنهاد پایان یافته است.")
    if hasattr(quotation, "customer_response"):
        raise QuotationResponseError("پاسخ این پیشنهاد قبلاً ثبت شده است.")
    if response == SalesQuotationResponse.ResponseType.REVISION_REQUESTED and not note.strip():
        raise QuotationResponseError({"note": "برای درخواست اصلاح، توضیحات الزامی است."})

    saved = SalesQuotationResponse.objects.create(
        quotation=quotation,
        customer=customer,
        response=response,
        note=note.strip(),
    )
    if response == SalesQuotationResponse.ResponseType.REVISION_REQUESTED:
        RequestForQuotation.objects.filter(
            pk=quotation.rfq_id,
            status__in=(RequestForQuotation.Status.QUOTED, RequestForQuotation.Status.SUBMITTED),
        ).update(status=RequestForQuotation.Status.UNDER_REVIEW)
    from apps.notifications.services import notify_quotation_response
    notify_quotation_response(quotation, saved)
    return saved
