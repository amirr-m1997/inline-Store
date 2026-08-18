import logging
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, serializers
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .google_auth import verify_google_credential
from .models import CustomerAddress, GoogleIdentity, PhoneOTP, User, normalize_iranian_phone
from .sms import send_otp

logger = logging.getLogger("accounts")


class AuthThrottle(AnonRateThrottle): scope = "auth"
class OTPThrottle(AnonRateThrottle): scope = "otp"


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source="phone", allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "phone_number", "landline", "customer_type", "company_name", "national_id", "economic_code", "job_title", "province", "city", "postal_code", "address", "date_joined")
        read_only_fields = ("id", "date_joined")

    def validate_email(self, value):
        value = value.strip().lower() if value else None
        if value and User.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return value


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ("id", "title", "recipient_name", "recipient_phone", "province", "city", "postal_code", "address", "is_default")
        read_only_fields = ("id",)

    def validate_recipient_phone(self, value):
        try: return normalize_iranian_phone(value)
        except DjangoValidationError as error: raise serializers.ValidationError(error.messages[0])

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default"):
            user.delivery_addresses.update(is_default=False)
        return CustomerAddress.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_default"):
            instance.user.delivery_addresses.exclude(pk=instance.pk).update(is_default=False)
        return super().update(instance, validated_data)

    def validate_phone_number(self, value):
        if not value: return None
        try: value = normalize_iranian_phone(value)
        except DjangoValidationError as error: raise serializers.ValidationError(error.messages[0])
        if User.objects.exclude(pk=self.instance.pk if self.instance else None).filter(phone=value).exists():
            raise serializers.ValidationError("این شماره موبایل قبلاً ثبت شده است.")
        return value


def profile_data(user): return ProfileSerializer(user).data

def auth_response(user, status=200):
    token, _ = Token.objects.get_or_create(user=user)
    response = Response({"customer": profile_data(user)}, status=status)
    response.set_cookie(settings.AUTH_COOKIE_NAME, token.key, httponly=True, secure=settings.AUTH_COOKIE_SECURE, samesite=settings.AUTH_COOKIE_SAMESITE, max_age=60 * 60 * 24 * 30, path="/")
    return response

def normalized_identifier(value):
    value = (value or "").strip()
    if "@" in value: return "email", value.lower()
    try: return "phone", normalize_iranian_phone(value)
    except DjangoValidationError: return None, None

def validate_new_password(password, user=None):
    try: validate_password(password, user)
    except DjangoValidationError as error: raise serializers.ValidationError({"password": error.messages})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([AuthThrottle])
def register(request):
    first_name, last_name = str(request.data.get("first_name", "")).strip(), str(request.data.get("last_name", "")).strip()
    email, phone = str(request.data.get("email", "")).strip().lower() or None, request.data.get("phone_number") or request.data.get("phone")
    password, confirm = request.data.get("password", ""), request.data.get("password_confirm", "")
    errors = {}
    if not first_name: errors["first_name"] = ["نام الزامی است."]
    if not last_name: errors["last_name"] = ["نام خانوادگی الزامی است."]
    if password != confirm: errors["password_confirm"] = ["تکرار رمز عبور مطابقت ندارد."]
    if not email and not phone: errors["identity"] = ["ایمیل یا شماره موبایل الزامی است."]
    if email:
        field = serializers.EmailField()
        try: email = field.run_validation(email)
        except serializers.ValidationError: errors["email"] = ["ایمیل معتبر نیست."]
    if phone:
        try: phone = normalize_iranian_phone(phone)
        except DjangoValidationError as error: errors["phone_number"] = error.messages
    if email and User.objects.filter(email=email).exists(): errors["email"] = ["این ایمیل قبلاً ثبت شده است."]
    if phone and User.objects.filter(phone=phone).exists(): errors["phone_number"] = ["این شماره موبایل قبلاً ثبت شده است."]
    if errors: return Response(errors, status=400)
    validate_new_password(password)
    user = User(username=f"customer_{uuid.uuid4().hex}", first_name=first_name, last_name=last_name, email=email, phone=phone, company_name=str(request.data.get("company_name", "")).strip())
    user.set_password(password); user.save()
    return auth_response(user, 201)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([AuthThrottle])
def login(request):
    kind, identity = normalized_identifier(request.data.get("identifier") or request.data.get("username"))
    user = User.objects.filter(**{kind: identity}).first() if kind else None
    if not user or not user.is_active or not user.check_password(request.data.get("password", "")):
        return Response({"detail": "اطلاعات ورود صحیح نیست."}, status=400)
    return auth_response(user)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([OTPThrottle])
def otp_request(request):
    try: phone = normalize_iranian_phone(request.data.get("phone_number", ""))
    except DjangoValidationError: return Response({"phone_number": ["شماره موبایل معتبر نیست."]}, status=400)
    purpose = request.data.get("purpose", PhoneOTP.Purpose.LOGIN)
    if purpose not in PhoneOTP.Purpose.values: return Response({"purpose": ["هدف درخواست نامعتبر است."]}, status=400)
    latest = PhoneOTP.objects.filter(phone=phone, purpose=purpose).first()
    if latest and latest.created_at > timezone.now() - timedelta(seconds=settings.OTP_RESEND_SECONDS):
        return Response({"detail": "لطفاً پیش از درخواست مجدد کمی صبر کنید."}, status=429)
    code = f"{secrets.randbelow(1000000):06d}"
    from django.contrib.auth.hashers import make_password
    PhoneOTP.objects.create(phone=phone, purpose=purpose, code_hash=make_password(code), expires_at=timezone.now() + timedelta(seconds=settings.OTP_EXPIRY_SECONDS))
    send_otp(phone, code)
    return Response({"detail": "در صورت معتبر بودن شماره، کد ارسال شد.", "expires_in": settings.OTP_EXPIRY_SECONDS})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([OTPThrottle])
def otp_verify(request):
    try: phone = normalize_iranian_phone(request.data.get("phone_number", ""))
    except DjangoValidationError: return Response({"detail": "کد یا شماره معتبر نیست."}, status=400)
    purpose = request.data.get("purpose", PhoneOTP.Purpose.LOGIN)
    from django.contrib.auth.hashers import check_password
    with transaction.atomic():
        otp = PhoneOTP.objects.select_for_update().filter(phone=phone, purpose=purpose, consumed_at__isnull=True).first()
        if not otp or otp.expires_at <= timezone.now() or otp.attempts >= otp.max_attempts:
            return Response({"detail": "کد منقضی یا نامعتبر است."}, status=400)
        if not check_password(str(request.data.get("code", "")), otp.code_hash):
            otp.attempts += 1; otp.save(update_fields=["attempts"])
            return Response({"detail": "کد منقضی یا نامعتبر است.", "remaining_attempts": max(0, otp.max_attempts - otp.attempts)}, status=400)
        otp.consumed_at = timezone.now(); otp.save(update_fields=["consumed_at"])
    if purpose == PhoneOTP.Purpose.PASSWORD_RESET:
        user = User.objects.filter(phone=phone, is_active=True).first()
        if not user: return Response({"detail": "کد تأیید شد."})
        token = signing.dumps({"user_id": user.id, "purpose": "password_reset", "password_hash": user.password}, salt="phone-password-reset")
        return Response({"reset_token": token})
    user, created = User.objects.get_or_create(phone=phone, defaults={"username": f"customer_{uuid.uuid4().hex}"})
    return auth_response(user, 201 if created else 200)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([AuthThrottle])
def google_login(request):
    payload = verify_google_credential(request.data.get("credential", ""))
    subject, email = payload["sub"], payload["email"].strip().lower()
    identity = GoogleIdentity.objects.select_related("user").filter(subject=subject).first()
    if identity: return auth_response(identity.user)
    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create(username=f"customer_{uuid.uuid4().hex}", email=email, first_name=payload.get("given_name", ""), last_name=payload.get("family_name", ""))
        user.set_unusable_password(); user.save()
    GoogleIdentity.objects.create(user=user, subject=subject)
    return auth_response(user)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([AuthThrottle])
def password_forgot(request):
    kind, identity = normalized_identifier(request.data.get("identifier"))
    user = User.objects.filter(**{kind: identity}, is_active=True).first() if kind else None
    if kind == "email" and user:
        uid = urlsafe_base64_encode(force_bytes(user.pk)); token = default_token_generator.make_token(user)
        link = f"{settings.FRONTEND_URL}/fa/reset-password?uid={uid}&token={token}"
        try:
            send_mail("بازیابی رمز عبور", link, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception as exc:
            logger.warning("password reset email failed user=%s error=%s", user.email, str(exc))
    return Response({"detail": "اگر حسابی با این مشخصات وجود داشته باشد، راهنمای بازیابی ارسال می‌شود.", "method": "otp" if kind == "phone" else "email"})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([AuthThrottle])
def password_reset(request):
    user = None
    reset_token = request.data.get("reset_token")
    if reset_token:
        try:
            data = signing.loads(reset_token, salt="phone-password-reset", max_age=600)
            user = User.objects.filter(pk=data["user_id"], is_active=True).first()
            if user and data.get("password_hash") != user.password: user = None
        except (signing.BadSignature, signing.SignatureExpired, KeyError): pass
    else:
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get("uid", ""))), is_active=True)
            if not default_token_generator.check_token(user, request.data.get("token", "")): user = None
        except (User.DoesNotExist, ValueError, TypeError): user = None
    if not user: return Response({"detail": "توکن بازیابی منقضی یا نامعتبر است."}, status=400)
    password = request.data.get("password", "")
    if password != request.data.get("password_confirm", ""): return Response({"password_confirm": ["تکرار رمز عبور مطابقت ندارد."]}, status=400)
    validate_new_password(password, user); user.set_password(password); user.save(update_fields=["password", "updated_at"]); Token.objects.filter(user=user).delete()
    return Response({"detail": "رمز عبور با موفقیت تغییر کرد."})


@api_view(["POST"])
def logout(request):
    if request.auth: request.auth.delete()
    response = Response(status=204); response.delete_cookie(settings.AUTH_COOKIE_NAME, path="/"); return response


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    if request.method == "PATCH":
        serializer = ProfileSerializer(request.user, data=request.data, partial=True); serializer.is_valid(raise_exception=True); serializer.save()
    return Response(profile_data(request.user))


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def session_status(request):
    if not request.user.is_authenticated:
        return Response({"authenticated": False, "customer": None})
    return Response({"authenticated": True, "customer": profile_data(request.user)})


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def addresses(request):
    if request.method == "POST":
        serializer = CustomerAddressSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True); serializer.save()
        return Response(serializer.data, status=201)
    return Response(CustomerAddressSerializer(request.user.delivery_addresses.all(), many=True).data)


@api_view(["PATCH", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def address_detail(request, address_id):
    address = request.user.delivery_addresses.filter(pk=address_id).first()
    if not address: return Response({"detail": "نشانی یافت نشد."}, status=404)
    if request.method == "DELETE": address.delete(); return Response(status=204)
    serializer = CustomerAddressSerializer(address, data=request.data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True); serializer.save(); return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def password_change(request):
    if not request.user.check_password(request.data.get("current_password", "")):
        return Response({"current_password": ["رمز عبور فعلی صحیح نیست."]}, status=400)
    password = request.data.get("password", "")
    if password != request.data.get("password_confirm", ""):
        return Response({"password_confirm": ["تکرار رمز عبور مطابقت ندارد."]}, status=400)
    validate_new_password(password, request.user)
    request.user.set_password(password); request.user.save(update_fields=("password", "updated_at"))
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "رمز عبور تغییر کرد؛ لطفاً دوباره وارد شوید."})
