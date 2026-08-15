from django.contrib import admin
from django.db.models import Count
from django.http import FileResponse, Http404
from django.urls import path, reverse

from .models import RequestForQuotation, RequestForQuotationItem, SalesQuotation, SalesQuotationItem, SalesQuotationResponse
from .services import generate_quotation_pdf


class RequestForQuotationItemInline(admin.TabularInline):
    model = RequestForQuotationItem
    extra = 0
    fields = ("product", "requested_quantity", "customer_note", "product_code_snapshot", "product_name_snapshot")
    readonly_fields = ("product_code_snapshot", "product_name_snapshot")
    autocomplete_fields = ("product",)


@admin.register(RequestForQuotation)
class RequestForQuotationAdmin(admin.ModelAdmin):
    list_display = ("reference", "contact_name", "company_name", "status", "quotation_response", "item_count", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "contact_name", "company_name", "phone", "email", "subject", "message")
    readonly_fields = ("reference", "created_at", "updated_at", "item_count")
    autocomplete_fields = ("customer",)
    inlines = (RequestForQuotationItemInline,)
    date_hierarchy = "created_at"
    fieldsets = (
        ("اطلاعات درخواست مشتری", {"fields": ("reference", "customer", "company_name", "contact_name", "phone", "email", "subject", "message", "preferred_contact_method", "source")}),
        ("گردش کار داخلی", {"fields": ("status", "internal_notes")}),
        ("اطلاعات زمانی", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="تعداد اقلام")
    def item_count(self, obj):
        return getattr(obj, "_item_count_value", obj.items.count())

    @admin.display(description="پاسخ پیشنهاد")
    def quotation_response(self, obj):
        quotation = getattr(obj, "quotation", None)
        response = getattr(quotation, "customer_response", None) if quotation and quotation.status == SalesQuotation.Status.ISSUED else None
        return response.get_response_display() if response else "در انتظار پاسخ"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_item_count_value=Count("items")).order_by("-created_at")

    @admin.action(description="ایجاد پیش‌نویس پیشنهاد برای یک استعلام")
    def create_quotation_draft(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "این عملیات فقط برای یک استعلام در هر بار مجاز است.", level="error")
            return
        rfq = queryset.first()
        quotation, created = SalesQuotation.objects.get_or_create(rfq=rfq, defaults={"created_by": request.user})
        if created:
            SalesQuotationItem.objects.bulk_create([
                SalesQuotationItem(
                    quotation=quotation, source_rfq_item=item, product=item.product,
                    product_name_snapshot=item.product_name_snapshot, product_code_snapshot=item.product_code_snapshot,
                    quantity=item.requested_quantity, unit_price=0,
                ) for item in rfq.items.select_related("product").all()
            ])
            self.message_user(request, f"پیش‌نویس {quotation.reference} ایجاد شد؛ قیمت‌ها باید توسط کارشناس تکمیل شوند.")
        else:
            self.message_user(request, f"برای این استعلام قبلاً {quotation.reference} ایجاد شده است.", level="warning")

    actions = ("create_quotation_draft",)


class SalesQuotationItemInline(admin.TabularInline):
    model = SalesQuotationItem
    extra = 0
    fields = ("source_rfq_item", "product", "product_name_snapshot", "product_code_snapshot", "quantity", "unit_price", "line_total")
    readonly_fields = ("product_name_snapshot", "product_code_snapshot", "line_total")
    autocomplete_fields = ("product",)

    @admin.display(description="جمع قلم")
    def line_total(self, obj):
        return obj.line_total


@admin.register(SalesQuotation)
class SalesQuotationAdmin(admin.ModelAdmin):
    list_display = ("reference", "rfq_reference", "customer", "status", "customer_response", "response_at", "currency", "subtotal", "issued_at", "created_at", "pdf_link")
    list_filter = ("status", "currency", "issued_at", "created_at", "customer_response__response")
    search_fields = ("reference", "rfq__reference", "rfq__contact_name", "rfq__company_name", "rfq__email")
    readonly_fields = ("reference", "rfq", "created_by", "created_at", "updated_at", "issued_at", "subtotal")
    autocomplete_fields = ("rfq", "created_by")
    inlines = (SalesQuotationItemInline,)
    date_hierarchy = "created_at"
    fieldsets = (
        ("اطلاعات پیشنهاد", {"fields": ("reference", "rfq", "status", "currency", "issued_at", "expires_at")}),
        ("یادداشت‌ها", {"fields": ("public_note", "internal_notes")}),
        ("پاسخ مشتری", {"fields": ("customer_response", "response_at", "response_note")}),
        ("اطلاعات داخلی", {"fields": ("created_by", "source", "subtotal", "created_at", "updated_at")}),
    )

    @admin.display(description="استعلام مرتبط")
    def rfq_reference(self, obj):
        return obj.rfq.reference

    @admin.display(description="مشتری")
    def customer(self, obj):
        return obj.rfq.customer or obj.rfq.contact_name

    @admin.display(description="جمع اقلام")
    def subtotal(self, obj):
        return obj.subtotal

    @admin.display(description="پاسخ مشتری")
    def customer_response(self, obj):
        try:
            return obj.customer_response.get_response_display()
        except SalesQuotationResponse.DoesNotExist:
            return "در انتظار پاسخ"

    @admin.display(description="زمان پاسخ")
    def response_at(self, obj):
        try:
            return obj.customer_response.response_at
        except SalesQuotationResponse.DoesNotExist:
            return None

    @admin.display(description="یادداشت پاسخ")
    def response_note(self, obj):
        try:
            return obj.customer_response.note or "—"
        except SalesQuotationResponse.DoesNotExist:
            return "—"

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj)) + ["customer_response", "response_at", "response_note"]
        if obj and obj.status == SalesQuotation.Status.ISSUED:
            fields.extend(("rfq", "status", "currency", "expires_at", "public_note", "internal_notes"))
        return tuple(dict.fromkeys(fields))

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = SalesQuotation.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if previous_status != SalesQuotation.Status.ISSUED and obj.status == SalesQuotation.Status.ISSUED:
            from apps.notifications.services import notify_quotation_issued
            notify_quotation_issued(obj)

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        if obj.status != SalesQuotation.Status.ISSUED:
            return "—"
        return f"/admin/rfq/salesquotation/{obj.pk}/pdf/"

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("<int:object_id>/pdf/", self.admin_site.admin_view(self.pdf_view), name="rfq_salesquotation_pdf")]
        return custom + urls

    def pdf_view(self, request, object_id):
        quotation = SalesQuotation.objects.filter(pk=object_id, status=SalesQuotation.Status.ISSUED).select_related("rfq").prefetch_related("items").first()
        if not quotation:
            raise Http404
        if not self.has_view_permission(request, quotation):
            raise Http404
        content = generate_quotation_pdf(quotation, locale="fa")
        return FileResponse(__import__("io").BytesIO(content), as_attachment=True, filename=f"quotation-{quotation.reference}.pdf", content_type="application/pdf")
