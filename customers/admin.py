"""ادمین مشتریان سازمانی: حساب، کاربران، آدرس‌ها و اعتبار."""
from __future__ import annotations

from django.contrib import admin, messages
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.admin_utils import ModelHelpMixin, PanelModelAdmin, badge, html_table, money_compact, progress_bar
from core.utils import jalali, num

from .models import Company, CompanyAddress, CompanyUser
from .services import aging_report, credit_snapshot
from core.palette import ACCENT, DANGER, INFO, OK, VIOLET, WARN


class CompanyUserInline(TabularInline):
    model = CompanyUser
    extra = 0
    autocomplete_fields = ("user",)
    fields = ("user", "role", "job_title", "phone", "approval_limit", "is_active", "can_view_invoices")
    verbose_name_plural = "کاربران خرید این حساب"
    tab = True


class CompanyAddressInline(TabularInline):
    model = CompanyAddress
    extra = 0
    fields = ("title", "province", "city", "address", "postal_code", "contact_name",
              "contact_phone", "is_default")
    verbose_name_plural = "آدرس‌های تحویل"
    tab = True


class CompanyResource(resources.ModelResource):
    """ورود/خروج اکسل مشتریان (با شناسه ملی به‌عنوان کلید)."""

    class Meta:
        model = Company
        fields = ("id", "name", "legal_type", "national_id", "economic_code", "phone", "mobile",
                  "email", "province", "city", "address", "postal_code", "price_list__code",
                  "payment_terms", "credit_limit", "credit_days", "sales_rep__username",
                  "kyc_status", "is_active")
        import_id_fields = ("national_id",)
        skip_unchanged = True


@admin.register(Company)
class CompanyAdmin(ModelHelpMixin, ImportExportModelAdmin, ModelAdmin):
    resource_class = CompanyResource
    import_form_class = ImportForm
    export_form_class = ExportForm
    compressed_fields = True
    list_fullwidth = True
    list_per_page = 30
    save_on_top = True

    list_display = ("name", "legal_type_badge", "province", "price_list", "sales_rep_name",
                    "credit_col", "credit_usage_col", "kyc_badge", "orders_count", "is_active")
    list_display_links = ("name",)
    list_filter = (("province", ChoicesDropdownFilter), ("payment_terms", ChoicesDropdownFilter),
                   ("kyc_status", ChoicesDropdownFilter), ("price_list", RelatedDropdownFilter),
                   "legal_type", "is_active", "is_blacklisted")
    search_fields = ("name", "national_id", "economic_code", "phone", "mobile", "email", "city")
    autocomplete_fields = ("price_list", "sales_rep", "parent")
    inlines = [CompanyUserInline, CompanyAddressInline]
    readonly_fields = ("credit_snapshot_display", "aging_display", "created_at", "updated_at")
    actions = ["action_approve_kyc", "action_blacklist_on", "action_blacklist_off"]
    fieldsets = (
        ("هویت", {
            "fields": (("name", "legal_type", "parent"),
                       ("national_id", "economic_code", "registration_number", "national_card")),
        }),
        ("تماس و نشانی", {
            "fields": (("phone", "mobile"), "email", ("province", "city"),
                       "address", "postal_code"),
        }),
        ("شرایط تجاری", {
            "fields": (("price_list", "sales_rep"), ("payment_terms", "credit_limit", "credit_days"),
                       ("requires_po", "vat_exempt")),
            "description": "سطح قیمت تعیین می‌کند مشتری کدام قیمت‌ها را ببیند؛ سقف اعتبار در ثبت سفارش کنترل می‌شود.",
        }),
        ("اعتبار و مطالبات", {"fields": ("credit_snapshot_display", "aging_display")}),
        ("احراز و وضعیت", {"fields": ("kyc_status", "kyc_note", "is_active", "is_blacklisted", "note")}),
        ("ردیابی", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # -------------------------------------------------- ستون‌ها
    @admin.display(description="نوع", ordering="legal_type")
    def legal_type_badge(self, obj):
        return badge(obj.get_legal_type_display(),
                     key="primary" if obj.legal_type == "legal" else "violet")

    @admin.display(description="کارشناس فروش", ordering="sales_rep__first_name")
    def sales_rep_name(self, obj):
        if not obj.sales_rep_id:
            return badge("تخصیص نیافته", key="warn")
        return obj.sales_rep.get_full_name() or obj.sales_rep.username

    @admin.display(description="سقف اعتبار", ordering="credit_limit")
    def credit_col(self, obj):
        if not obj.credit_limit:
            return badge("نقدی", key="muted")
        return money_compact(obj.credit_limit)

    @admin.display(description="مصرف اعتبار")
    def credit_usage_col(self, obj):
        if not obj.credit_limit:
            return "—"
        pct = obj.credit_usage_pct
        color = DANGER if pct >= 100 else (WARN if pct >= 80 else ACCENT)
        return progress_bar(pct, color)

    @admin.display(description="KYC", ordering="kyc_status")
    def kyc_badge(self, obj):
        return badge(obj.get_kyc_status_display(), color=obj.kyc_color)

    @admin.display(description="سفارش‌ها")
    def orders_count(self, obj):
        return num(obj.orders.count())

    # -------------------------------------------------- فیلدهای readonly
    @admin.display(description="وضعیت اعتبار")
    def credit_snapshot_display(self, obj):
        if not obj.pk:
            return "—"
        snapshot = credit_snapshot(obj)
        rows = [
            ["سقف اعتبار", num(snapshot["limit"], 0)],
            ["مانده فاکتورهای باز", num(snapshot["receivable"], 0)],
            ["چک‌های در جریان", num(snapshot["cheques"], 0)],
            ["اعتبار آزاد", num(snapshot["available"], 0)],
            ["درصد مصرف", f"{num(snapshot['usage_pct'], 0)}٪"],
            ["فاکتورهای باز / معوق", f"{num(snapshot['open_invoices'], 0)} / {num(snapshot['overdue_invoices'], 0)}"],
        ]
        label, color = obj.credit_status
        return format_html("{}<div style='margin-top:8px'>{}</div>", badge(label, color=color),
                           html_table(["شرح", "مبلغ (تومان)"], rows))

    @admin.display(description="سنّی‌بندی مطالبات")
    def aging_display(self, obj):
        if not obj.pk:
            return "—"
        buckets = aging_report(obj)
        rows = [
            ["۰ تا ۳۰ روز", num(buckets["0_30"], 0)],
            ["۳۱ تا ۶۰ روز", num(buckets["31_60"], 0)],
            ["۶۱ تا ۹۰ روز", num(buckets["61_90"], 0)],
            ["بیش از ۹۰ روز", num(buckets["90_plus"], 0)],
            ["جمع", num(buckets["total"], 0)],
        ]
        return html_table(["بازه", "مانده (تومان)"], rows)

    # -------------------------------------------------- اکشن‌ها
    @admin.action(description="تأیید احراز هویت (KYC)")
    def action_approve_kyc(self, request, queryset):
        updated = queryset.update(kyc_status="approved")
        self.message_user(request, f"{num(updated)} حساب تأیید شد.", messages.SUCCESS)

    @admin.action(description="افزودن به لیست سیاه")
    def action_blacklist_on(self, request, queryset):
        queryset.update(is_blacklisted=True)

    @admin.action(description="حذف از لیست سیاه")
    def action_blacklist_off(self, request, queryset):
        queryset.update(is_blacklisted=False)

    # -------------------------------------------------- دسترسی سطح شیء
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("price_list", "sales_rep")
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "sales":  # کارشناس فروش فقط مشتریان خودش
            qs = qs.filter(sales_rep=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CompanyUser)
class CompanyUserAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("company", "user")
    list_display = ("user", "company", "role_badge", "job_title", "approval_limit_col",
                    "is_active", "can_view_invoices")
    list_filter = (("role", ChoicesDropdownFilter), ("company", RelatedDropdownFilter), "is_active")
    search_fields = ("user__username", "user__first_name", "user__last_name", "company__name")
    autocomplete_fields = ("company", "user")
    readonly_fields = ("invited_at",)

    @admin.display(description="نقش", ordering="role")
    def role_badge(self, obj):
        color = {"buyer": ACCENT, "approver": VIOLET, "finance": OK,
                 "admin": INFO}.get(obj.role)
        return badge(obj.get_role_display(), color=color)

    @admin.display(description="سقف تأیید", ordering="approval_limit")
    def approval_limit_col(self, obj):
        return money_compact(obj.approval_limit) if obj.approval_limit else badge("بدون تأیید", key="muted")


@admin.register(CompanyAddress)
class CompanyAddressAdmin(PanelModelAdmin, ModelAdmin):
    list_select_related = ("company",)
    list_display = ("company", "title", "province", "city", "contact_name", "contact_phone",
                    "is_default", "loading_note")
    list_filter = (("province", ChoicesDropdownFilter), "is_default",
                   ("company", RelatedDropdownFilter))
    search_fields = ("company__name", "title", "address", "contact_name", "contact_phone")
    autocomplete_fields = ("company",)
