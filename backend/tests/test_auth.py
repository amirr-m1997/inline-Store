from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import CustomerAddress, PhoneOTP, User


@override_settings(OTP_RESEND_SECONDS=0, OTP_EXPIRY_SECONDS=120)
class CustomerAuthenticationTests(TestCase):
    password = "Strong-pass-123!"

    def setUp(self):
        cache.clear()

    def register(self, **overrides):
        payload = {"first_name": "امیر", "last_name": "محمدی", "email": "USER@Example.COM", "password": self.password, "password_confirm": self.password}
        payload.update(overrides)
        return self.client.post("/api/v1/auth/register/", payload, content_type="application/json")

    def test_registration_with_email_normalizes_identity_and_sets_cookie(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get().email, "user@example.com")
        self.assertIn("mehrasl_auth", response.cookies)
        self.assertTrue(User.objects.get().check_password(self.password))

    def test_registration_with_phone_only(self):
        response = self.register(email="", phone_number="09121234567")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get().phone, "+989121234567")
        self.assertIsNone(User.objects.get().email)

    def test_duplicate_email_and_normalized_phone_are_rejected(self):
        self.register(phone_number="09121234567")
        self.client.cookies.clear()
        self.assertEqual(self.register(email="user@example.com").status_code, 400)
        self.assertEqual(self.register(email="other@example.com", phone_number="00989121234567").status_code, 400)

    def test_password_login_profile_and_logout(self):
        self.register(phone_number="09121234567")
        self.client.cookies.clear()
        invalid = self.client.post("/api/v1/auth/login/", {"identifier": "09121234567", "password": "wrong"}, content_type="application/json")
        self.assertEqual(invalid.status_code, 400)
        login = self.client.post("/api/v1/auth/login/", {"identifier": "+989121234567", "password": self.password}, content_type="application/json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/profile/").status_code, 200)
        logout = self.client.post("/api/v1/auth/logout/")
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/profile/").status_code, 401)

    def test_customer_can_update_extended_profile(self):
        self.register(phone_number="09121234567")
        response = self.client.patch("/api/v1/auth/profile/", {"customer_type": "business", "company_name": "صنایع نمونه", "economic_code": "411111", "job_title": "مدیر خرید", "landline": "02112345678"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["economic_code"], "411111")

    def test_customer_address_is_scoped_to_authenticated_user(self):
        self.register(phone_number="09121234567")
        payload = {"title": "دفتر", "recipient_name": "امیر محمدی", "recipient_phone": "09121234567", "province": "تهران", "city": "تهران", "postal_code": "1234567890", "address": "نشانی آزمایشی", "is_default": True}
        created = self.client.post("/api/v1/auth/addresses/", payload, content_type="application/json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["recipient_phone"], "+989121234567")
        self.assertEqual(self.client.get("/api/v1/auth/addresses/").json()[0]["title"], "دفتر")
        other = User.objects.create_user(username="other", email="other@example.com", password=self.password)
        foreign = CustomerAddress.objects.create(user=other, **{**payload, "recipient_phone": "+989121234567"})
        self.assertEqual(self.client.delete(f"/api/v1/auth/addresses/{foreign.id}/").status_code, 404)

    def test_authenticated_customer_can_change_password(self):
        self.register()
        response = self.client.post("/api/v1/auth/password/change/", {"current_password": self.password, "password": "New-strong-456!", "password_confirm": "New-strong-456!"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get().check_password("New-strong-456!"))

    @patch("apps.accounts.api.send_otp")
    @patch("apps.accounts.api.secrets.randbelow", return_value=12345)
    def test_otp_request_incorrect_attempt_expiry_and_success(self, random_mock, send_mock):
        requested = self.client.post("/api/v1/auth/otp/request/", {"phone_number": "09121234567"}, content_type="application/json")
        self.assertEqual(requested.status_code, 200)
        send_mock.assert_called_once_with("+989121234567", "012345")
        incorrect = self.client.post("/api/v1/auth/otp/verify/", {"phone_number": "09121234567", "code": "000000"}, content_type="application/json")
        self.assertEqual(incorrect.status_code, 400)
        self.assertEqual(PhoneOTP.objects.get().attempts, 1)
        success = self.client.post("/api/v1/auth/otp/verify/", {"phone_number": "09121234567", "code": "012345"}, content_type="application/json")
        self.assertEqual(success.status_code, 201)
        self.assertIsNotNone(PhoneOTP.objects.get().consumed_at)
        PhoneOTP.objects.create(phone="+989131234567", purpose="login", code_hash=PhoneOTP.objects.get().code_hash, expires_at=timezone.now() - timedelta(seconds=1))
        expired = self.client.post("/api/v1/auth/otp/verify/", {"phone_number": "09131234567", "code": "012345"}, content_type="application/json")
        self.assertEqual(expired.status_code, 400)

    @patch("apps.accounts.api.send_otp")
    @patch("apps.accounts.api.secrets.randbelow", return_value=12345)
    def test_phone_password_reset(self, random_mock, send_mock):
        user = User.objects.create_user(username="phone-user", phone="09121234567", password=self.password)
        self.client.post("/api/v1/auth/otp/request/", {"phone_number": user.phone, "purpose": "password_reset"}, content_type="application/json")
        verified = self.client.post("/api/v1/auth/otp/verify/", {"phone_number": user.phone, "code": "012345", "purpose": "password_reset"}, content_type="application/json")
        reset = self.client.post("/api/v1/auth/password/reset/", {"reset_token": verified.json()["reset_token"], "password": "New-strong-456!", "password_confirm": "New-strong-456!"}, content_type="application/json")
        self.assertEqual(reset.status_code, 200)
        user.refresh_from_db(); self.assertTrue(user.check_password("New-strong-456!"))
        reused = self.client.post("/api/v1/auth/password/reset/", {"reset_token": verified.json()["reset_token"], "password": "Another-strong-789!", "password_confirm": "Another-strong-789!"}, content_type="application/json")
        self.assertEqual(reused.status_code, 400)

    @patch("apps.accounts.api.verify_google_credential", return_value={"sub": "google-sub", "email": "google@example.com", "email_verified": True, "given_name": "Google", "family_name": "User"})
    def test_google_identity_is_verified_at_boundary(self, verify_mock):
        response = self.client.post("/api/v1/auth/google/", {"credential": "signed-google-token"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["customer"]["email"], "google@example.com")
        verify_mock.assert_called_once_with("signed-google-token")
