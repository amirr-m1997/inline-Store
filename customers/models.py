"""مشتریان سازمانی: حساب حقوقی/حقیقی، کاربران خرید، آدرس‌ها و اعتبار."""
from __future__ import annotations

from django.conf import settings
from django.db import models

LEGAL_TYPES = [("legal", "شخص حقوقی"), ("person", "شخص حقیقی")]
KYC_STATUS = [("pending", "در انتظار بررسی"), ("approved", "تأییدشده"), ("rejected", "ردشده")]
PAYMENT_TERMS = [
    ("cash", "نقدی"),
    ("prepay", "پیش‌پرداخت"),
    ("cheque", "چک (با سررسید)"),
    ("net30", "اعتباری ۳۰ روزه"),
    ("net60", "اعتباری ۶۰ روزه"),
    ("credit", "اعتباری داخلی"),
    ("mixed", "ترکیبی (پیش‌پرداخت + چک)"),
]
COMPANY_USER_ROLES = [
    ("buyer", "خریدار"),
    ("approver", "تأییدکننده"),
    ("finance", "مالی"),
    ("admin", "مدیر حساب"),
]
PROVINCES = [
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "اصفهان", "البرز", "ایلام", "بوشهر",
    "تهران", "چهارمحال و بختیاری", "خراسان جنوبی", "خراسان رضوی", "خراسان شمالی", "خوزستان",
    "زنجان", "سمنان", "سیستان و بلوچستان", "فارس", "قزوین", "قم", "کردستان", "کرمان",
    "کرمانشاه", "کهگیلویه و بویراحمد", "گلستان", "گیلان", "لرستان", "مازندران", "مرکزی",
    "هرمزگان", "همدان", "یزد",
]


class Company(models.Model):
    """حساب سازمانی مشتری (پدر/فرزند) با سطح قیمت، اعتبار و کارشناس فروش."""

    name = models.CharField("نام شرکت/شخص", max_length=200)
    legal_type = models.CharField("نوع شخصیت", max_length=10, choices=LEGAL_TYPES, default="legal")
    parent = models.ForeignKey(
        "self", verbose_name="شرکت مادر", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="branches")
    national_id = models.CharField("شناسه ملی", max_length=15, blank=True)
    economic_code = models.CharField("کد اقتصادی", max_length=15, blank=True)
    registration_number = models.CharField("شماره ثبت", max_length=20, blank=True)
    national_card = models.CharField("کد ملی (اشخاص حقیقی)", max_length=12, blank=True)

    phone = models.CharField("تلفن", max_length=25, blank=True)
    mobile = models.CharField("همراه", max_length=20, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    website = models.CharField("وب‌سایت", max_length=120, blank=True)

    province = models.CharField("استان", max_length=40, choices=[(p, p) for p in PROVINCES], blank=True)
    city = models.CharField("شهر", max_length=60, blank=True)
    address = models.CharField("نشانی", max_length=255, blank=True)
    postal_code = models.CharField("کد پستی", max_length=12, blank=True)

    # تجاری
    price_list = models.ForeignKey(
        "pricing.PriceList", verbose_name="سطح قیمت", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="companies")
    payment_terms = models.CharField("شرایط تسویه", max_length=10, choices=PAYMENT_TERMS, default="cash")
    credit_limit = models.BigIntegerField("سقف اعتبار (تومان)", default=0)
    credit_days = models.PositiveIntegerField("مهلت پرداخت (روز)", default=0)
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="کارشناس فروش", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="customers")
    requires_po = models.BooleanField("الزام شماره سفارش خرید (PO)", default=True)
    vat_exempt = models.BooleanField("معاف از ارزش افزوده", default=False)

    kyc_status = models.CharField("وضعیت احراز (KYC)", max_length=10, choices=KYC_STATUS, default="pending",
                                  db_index=True)
    kyc_note = models.CharField("یادداشت احراز", max_length=200, blank=True)
    is_active = models.BooleanField("فعال", default=True, db_index=True)
    is_blacklisted = models.BooleanField("لیست سیاه", default=False)
    note = models.TextField("یادداشت داخلی", blank=True)

    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="companies_created")

    class Meta:
        verbose_name = "حساب سازمانی"
        verbose_name_plural = "حساب‌های سازمانی مشتریان"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["province"])]

    def __str__(self) -> str:
        return self.name

    # ---------------------------------------------------------- اعتبار
    @property
    def credit_used(self) -> int:
        """جمع مانده‌ی فاکتورهای باز + چک‌های در جریان — با ۲ کوئری، نه یکی‌به‌ازای هر سند.

        پیش‌تر برای هر فاکتور و هر چک یک کوئری جدا اجرا می‌شد؛ در داشبورد پنل که
        اعتبار ده‌ها مشتری را نشان می‌دهد این یعنی صدها کوئری. اینک هر دو جمع
        با یک aggregate گرفته می‌شود و نتیجه عددی یکسان است.
        """
        from django.db.models import BigIntegerField, F, Sum, Value
        from django.db.models.functions import Greatest

        from finance.models import Cheque, Invoice

        invoices = (Invoice.objects
                    .filter(company=self)
                    .exclude(status__in=["paid", "cancelled", "draft"])
                    .annotate(_balance=Greatest(F("total") - F("paid_amount"),
                                                Value(0), output_field=BigIntegerField()))
                    .aggregate(total=Sum("_balance"))["total"])
        cheques = (Cheque.objects
                   .filter(company=self, direction="received",
                           status__in=["in_hand", "deposited"])
                   .aggregate(total=Sum("amount"))["total"])
        return int(invoices or 0) + int(cheques or 0)

    @property
    def credit_available(self) -> int:
        return max(self.credit_limit - self.credit_used, 0)

    @property
    def credit_usage_pct(self) -> int:
        if not self.credit_limit:
            return 0
        return min(round(self.credit_used * 100 / self.credit_limit), 150)

    @property
    def credit_status(self) -> tuple[str, str]:
        if not self.credit_limit:
            return "بدون سقف اعتبار", "#64748b"
        pct = self.credit_usage_pct
        if pct >= 100:
            return "عبور از سقف اعتبار", "#c02626"
        if pct >= 80:
            return "نزدیک سقف اعتبار", "#b45309"
        return "در محدوده مجاز", "#12855f"

    @property
    def kyc_color(self) -> str:
        return {"approved": "#12855f", "pending": "#b45309", "rejected": "#c02626"}.get(
            self.kyc_status, "#64748b")

    @property
    def is_legal(self) -> bool:
        return self.legal_type == "legal"

    @property
    def active_users(self):
        return self.users.filter(is_active=True).select_related("user")


class CompanyUser(models.Model):
    """کاربر خرید سازمانی زیرمجموعه‌ی یک حساب."""

    company = models.ForeignKey(Company, verbose_name="حساب سازمانی", on_delete=models.CASCADE,
                                related_name="users")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="کاربر",
                                on_delete=models.CASCADE, related_name="company_membership")
    role = models.CharField("نقش خرید", max_length=10, choices=COMPANY_USER_ROLES, default="buyer")
    job_title = models.CharField("سمت", max_length=80, blank=True)
    phone = models.CharField("تلفن", max_length=20, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    approval_limit = models.BigIntegerField("سقف تأیید سفارش (تومان)", default=0)
    is_active = models.BooleanField("فعال", default=True)
    can_view_invoices = models.BooleanField("دسترسی به فاکتورها", default=False)
    invited_at = models.DateTimeField("زمان دعوت", auto_now_add=True)

    class Meta:
        verbose_name = "کاربر مشتری"
        verbose_name_plural = "کاربران مشتریان"
        ordering = ["company", "role"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} — {self.company.name}"


class CompanyAddress(models.Model):
    company = models.ForeignKey(Company, verbose_name="حساب سازمانی", on_delete=models.CASCADE,
                                related_name="addresses")
    title = models.CharField("عنوان", max_length=80, help_text="مثلاً دفتر مرکزی، کارگاه پروژه A")
    province = models.CharField("استان", max_length=40,
                                choices=[(p, p) for p in PROVINCES], blank=True)
    city = models.CharField("شهر", max_length=60, blank=True)
    address = models.CharField("نشانی", max_length=255, blank=True)
    postal_code = models.CharField("کد پستی", max_length=12, blank=True)
    contact_name = models.CharField("نام رابط", max_length=100, blank=True)
    contact_phone = models.CharField("تلفن رابط", max_length=25, blank=True)
    is_default = models.BooleanField("پیش‌فرض", default=False)
    loading_note = models.CharField("ملاحظات تخلیه/بارگیری", max_length=200, blank=True)

    class Meta:
        verbose_name = "آدرس مشتری"
        verbose_name_plural = "آدرس‌های مشتریان"
        ordering = ["company", "-is_default", "title"]

    def __str__(self) -> str:
        return f"{self.company.name} — {self.title}"
