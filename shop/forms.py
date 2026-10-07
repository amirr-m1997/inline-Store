"""فرم‌های سایت مشتری: ثبت‌نام، ورود، پرداخت/ثبت سفارش، پروفایل و نشانی."""
from __future__ import annotations

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm as DjangoPasswordChangeForm,
    PasswordResetForm as DjangoPasswordResetForm,
    SetPasswordForm as DjangoSetPasswordForm,
    UserCreationForm,
)
from django.core.cache import cache
from django.utils import timezone

from customers.models import Company, CompanyAddress, CompanyUser, PROVINCES

User = get_user_model()

# کلاس‌های استایل از CSS خود سایت می‌آیند (static/css/shop.css) تا سایت بدون CDN هم کامل باشد.
INPUT = "form-input"


class ShopFormMixin:
    """کلاس‌های استایل مشترک برای همه‌ی فیلدهای فرم‌های سایت."""

    def style_fields(self) -> None:
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-check")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", INPUT)
            else:
                widget.attrs.setdefault("class", INPUT)
            if field.required:
                field.widget.attrs.setdefault("aria-required", "true")


# ---------------------------------------------------------------- ثبت‌نام
class SignupForm(ShopFormMixin, UserCreationForm):
    """ثبت‌نام مشتری سازمانی: حساب کاربر + حساب سازمانی (در انتظار تأیید)."""

    first_name = forms.CharField(label="نام", max_length=60)
    last_name = forms.CharField(label="نام خانوادگی", max_length=60)
    email = forms.EmailField(label="ایمیل", help_text="برای بازیابی گذرواژه و ارسال اسناد استفاده می‌شود.")
    mobile = forms.CharField(label="همراه", max_length=20)

    company_name = forms.CharField(label="نام شرکت / فروشگاه", max_length=200)
    legal_type = forms.ChoiceField(label="نوع شخصیت", choices=[("legal", "حقوقی"), ("real", "حقیقی")])
    national_id = forms.CharField(label="شناسه ملی", max_length=15, required=False,
                                  help_text="برای اشخاص حقوقی الزامی است.")
    economic_code = forms.CharField(label="کد اقتصادی", max_length=15, required=False)
    province = forms.ChoiceField(label="استان", choices=[("", "— انتخاب کنید —")] + [(p, p) for p in PROVINCES])
    city = forms.CharField(label="شهر", max_length=60)
    company_phone = forms.CharField(label="تلفن شرکت", max_length=25, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "نام کاربری"
        self.fields["username"].help_text = "با حروف انگلیسی؛ برای ورود به سایت."
        self.fields["password1"].label = "گذرواژه"
        self.fields["password2"].label = "تکرار گذرواژه"
        self.style_fields()

    def clean_mobile(self):
        mobile = (self.cleaned_data.get("mobile") or "").strip()
        digits = mobile.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")).replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) != 11 or not digits.startswith("09"):
            raise forms.ValidationError("شماره همراه باید ۱۱ رقم و با ۰۹ شروع شود.")
        return digits

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("این ایمیل قبلاً ثبت شده است. از «فراموشی گذرواژه» استفاده کنید.")
        return email

    def clean(self):
        data = super().clean()
        if data.get("legal_type") == "legal" and not (data.get("national_id") or "").strip():
            self.add_error("national_id", "برای شخصیت حقوقی، شناسهٔ ملی الزامی است.")
        if Company.objects.filter(name__iexact=(data.get("company_name") or "").strip()).exists():
            self.add_error("company_name", "شرکتی با این نام از قبل ثبت شده است؛ با پشتیبانی تماس بگیرید.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.is_staff = False
        user.is_active = True
        if commit:
            user.save()
            company = Company.objects.create(
                name=self.cleaned_data["company_name"].strip(),
                legal_type=self.cleaned_data["legal_type"],
                national_id=self.cleaned_data.get("national_id", ""),
                economic_code=self.cleaned_data.get("economic_code", ""),
                province=self.cleaned_data["province"],
                city=self.cleaned_data["city"],
                phone=self.cleaned_data.get("company_phone", ""),
                mobile=self.cleaned_data["mobile"],
                email=self.cleaned_data["email"],
                kyc_status="pending",
                is_active=True,
                note="ثبت‌نام خودکار از سایت مشتری — نیازمند بررسی و تأیید KYC",
            )
            CompanyUser.objects.create(
                company=company, user=user, role="admin", job_title="ثبت‌کنندهٔ حساب",
                phone=self.cleaned_data["mobile"], email=self.cleaned_data["email"],
                can_view_invoices=True, is_active=True,
            )
        return user


# ---------------------------------------------------------------- ورود
class LoginForm(ShopFormMixin, AuthenticationForm):
    """ورود با محدودیت تلاش ناموفق (ضدحمله‌ی جست‌وجوی گذرواژه)."""

    LOCK_AFTER = 5
    LOCK_MINUTES = 5

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].label = "نام کاربری یا ایمیل"
        self.fields["password"].label = "گذرواژه"
        self.style_fields()

    @staticmethod
    def _key(request) -> str:
        ip = request.META.get("REMOTE_ADDR", "unknown") if request else "unknown"
        username = (request.POST.get("username") or "").strip().lower() if request else ""
        return f"shop-login-fail:{ip}:{username}"

    def clean(self):
        request = getattr(self, "request", None)
        key = self._key(request)
        fails = cache.get(key, 0)
        if fails >= self.LOCK_AFTER:
            raise forms.ValidationError(
                f"تلاش‌های ناموفق زیاد بوده است؛ {self.LOCK_MINUTES} دقیقه بعد دوباره امتحان کنید."
            )
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            cache.set(key, fails + 1, self.LOCK_MINUTES * 60)
            raise
        cache.delete(key)
        return cleaned


# ---------------------------------------------------------------- پرداخت و ثبت سفارش
class CheckoutForm(ShopFormMixin, forms.Form):
    """فرم ثبت سفارش: شمارهٔ PO، پروژه، نشانی تحویل و روش پرداخت."""

    po_number = forms.CharField(label="شماره سفارش خرید (PO)", max_length=40, required=False)
    project_name = forms.CharField(label="نام پروژه / کاربرد", max_length=160, required=False)
    shipping_method = forms.ChoiceField(
        label="روش تحویل",
        choices=[("pickup", "تحویل از کارخانه (تبریز)"), ("delivery", "ارسال با باربری")],
    )
    address = forms.ModelChoiceField(label="نشانی تحویل", queryset=CompanyAddress.objects.none(), required=False)
    new_address_title = forms.CharField(label="یا نشانی جدید — عنوان", max_length=80, required=False)
    new_address_city = forms.CharField(label="شهر", max_length=60, required=False)
    new_address_text = forms.CharField(label="نشانی کامل", max_length=255, required=False)
    payment_method = forms.ChoiceField(label="روش پرداخت", choices=[])
    contact_phone = forms.CharField(label="تلفن هماهنگی", max_length=25, required=False)
    customer_note = forms.CharField(label="یادداشت برای کارشناس فروش", required=False,
                                    widget=forms.Textarea(attrs={"rows": 3}))
    accept_terms = forms.BooleanField(label="قواعد فروش و شرایط تسویه را می‌پذیرم.", required=True)

    def __init__(self, *args, company=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.user = user
        if company is not None:
            self.fields["address"].queryset = company.addresses.all()
            default = company.addresses.filter(is_default=True).first() or company.addresses.first()
            if default and not self.is_bound:
                self.fields["address"].initial = default.pk
            if company.requires_po:
                self.fields["po_number"].required = True
                self.fields["po_number"].help_text = "این مشتری برای ثبت سفارش باید شمارهٔ PO اعلام کند."
            methods = [("online", "پرداخت آنلاین (درگاه آزمایشی)")]
            if company.payment_terms in ("credit", "cheque"):
                methods.append(("credit", "خرید اعتباری / تسویه در سررسید"))
            if company.payment_terms == "cheque":
                methods.append(("cheque", "پرداخت با چک (تحویل چک به فروش)"))
            self.fields["payment_method"].choices = methods
        else:
            self.fields["payment_method"].choices = [("online", "پرداخت آنلاین")]
        self.style_fields()

    def clean(self):
        data = super().clean()
        if not data.get("address") and not (data.get("new_address_text") or "").strip():
            self.add_error("new_address_text", "یک نشانی تحویل انتخاب کنید یا نشانی جدید را وارد کنید.")
        return data

    def save_address(self) -> CompanyAddress | None:
        """اگر کاربر نشانی جدید وارد کرده باشد، آن را برای شرکت ثبت می‌کند."""
        if self.cleaned_data.get("address"):
            return self.cleaned_data["address"]
        title = (self.cleaned_data.get("new_address_title") or "نشانی جدید").strip()
        address = CompanyAddress.objects.create(
            company=self.company,
            title=title,
            city=self.cleaned_data.get("new_address_city", ""),
            address=self.cleaned_data.get("new_address_text", ""),
            contact_name=self.user.get_full_name() if self.user else "",
            contact_phone=self.cleaned_data.get("contact_phone", ""),
            is_default=not CompanyAddress.objects.filter(company=self.company).exists(),
        )
        return address


# ---------------------------------------------------------------- پروفایل
class ProfileForm(ShopFormMixin, forms.Form):
    first_name = forms.CharField(label="نام", max_length=60)
    last_name = forms.CharField(label="نام خانوادگی", max_length=60)
    email = forms.EmailField(label="ایمیل")
    phone = forms.CharField(label="تلفن همراه", max_length=20, required=False)
    job_title = forms.CharField(label="سمت", max_length=80, required=False,
                                help_text="مثلاً مدیر خرید، کارشناس تأسیسات")

    def __init__(self, *args, user=None, membership=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.membership = membership
        if user is not None and not self.is_bound:
            self.initial.update({
                "first_name": user.first_name, "last_name": user.last_name, "email": user.email,
                "phone": getattr(membership, "phone", ""),
                "job_title": getattr(membership, "job_title", ""),
            })
        self.style_fields()

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        if self.membership is not None:
            self.membership.phone = self.cleaned_data.get("phone", "")
            self.membership.job_title = self.cleaned_data.get("job_title", "")
            self.membership.save(update_fields=["phone", "job_title"])
        return self.user


class AddressForm(ShopFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyAddress
        fields = ("title", "province", "city", "address", "postal_code",
                  "contact_name", "contact_phone", "loading_note", "is_default")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["province"].choices = [("", "— انتخاب کنید —")] + [(p, p) for p in PROVINCES]
        self.style_fields()


class PaymentForm(ShopFormMixin, forms.Form):
    """فرم درگاه آزمایشی: انتخاب روش قدم بعدی (بدون ورود اطلاعات کارت)."""

    gateway = forms.ChoiceField(
        label="درگاه پرداخت",
        choices=[("mock-asan", "درگاه آزمایشی آسان‌پرداخت (شبیه‌سازی)"),
                 ("mock-tejarat", "درگاه آزمایشی بانک تجارت (شبیه‌سازی)")],
    )
    confirm = forms.BooleanField(label="مبلغ فاکتور را بررسی کردم و تأیید می‌کنم.", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean(self):
        data = super().clean()
        if not settings.SHOP_MOCK_GATEWAY:
            raise forms.ValidationError("درگاه پرداخت آنلاین در این نسخه فعال نیست.")
        return data


# ---------------------------------------------------------------- بازیابی گذرواژه
class PasswordResetForm(ShopFormMixin, DjangoPasswordResetForm):
    """فرم «فراموشی گذرواژه» با برچسب‌های فارسی و استایل سایت."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "ایمیل حساب کاربری"
        self.fields["email"].help_text = "نشانی بازیابی گذرواژه به همین ایمیل ارسال می‌شود."
        self.style_fields()


class SetPasswordForm(ShopFormMixin, DjangoSetPasswordForm):
    """تعیین گذرواژهٔ جدید (مرحلهٔ سوم بازیابی)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "گذرواژهٔ جدید"
        self.fields["new_password2"].label = "تکرار گذرواژهٔ جدید"
        self.style_fields()


class PasswordChangeForm(ShopFormMixin, DjangoPasswordChangeForm):
    """تغییر گذرواژهٔ کاربر وارد‌شده."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "گذرواژهٔ فعلی"
        self.fields["new_password1"].label = "گذرواژهٔ جدید"
        self.fields["new_password2"].label = "تکرار گذرواژهٔ جدید"
        self.style_fields()
