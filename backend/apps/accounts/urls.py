from django.urls import path
from . import api

urlpatterns = [
    path("register/", api.register), path("login/", api.login), path("logout/", api.logout), path("profile/", api.profile), path("session/", api.session_status),
    path("otp/request/", api.otp_request), path("otp/verify/", api.otp_verify), path("google/", api.google_login),
    path("password/forgot/", api.password_forgot), path("password/reset/", api.password_reset),
    path("password/change/", api.password_change), path("addresses/", api.addresses), path("addresses/<int:address_id>/", api.address_detail),
]
