"""مسیرهای سایت مشتری مهراصل."""
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

app_name = "shop"

urlpatterns = [
    # ---------------------------------------------------------------- کاتالوگ
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("p/<slug:slug>/", views.product_detail, name="product"),

    # ---------------------------------------------------------------- سبد خرید
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart-add"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart-update"),
    path("cart/clear/", views.cart_clear, name="cart-clear"),
    path("cart/rfq/", views.rfq_from_cart, name="rfq-from-cart"),

    # ---------------------------------------------------------------- ثبت سفارش و پرداخت
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="orders"),
    path("orders/<str:number>/", views.order_detail, name="order-detail"),
    path("invoices/<str:number>/", views.invoice_detail, name="invoice"),
    path("invoices/<str:number>/pay/", views.invoice_pay, name="invoice-pay"),
    path("invoices/<str:number>/paid/", views.payment_success, name="payment-success"),

    # ---------------------------------------------------------------- حساب کاربری
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="shop/login.html",
        authentication_form=LoginForm,
        redirect_authenticated_user=True,
    ), name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/profile/", views.profile, name="profile"),
    path("accounts/addresses/<int:pk>/delete/", views.address_delete, name="address-delete"),
    path("accounts/password/", auth_views.PasswordChangeView.as_view(
        template_name="shop/password_change.html",
        form_class=PasswordChangeForm,
        success_url=reverse_lazy("shop:password-change-done"),
    ), name="password-change"),
    path("accounts/password/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="shop/password_change_done.html"), name="password-change-done"),

    # بازیابی گذرواژه (چهار مرحله‌ی استاندارد جنگو با قالب‌های فارسی)
    path("accounts/reset/", auth_views.PasswordResetView.as_view(
        template_name="shop/password_reset.html",
        email_template_name="shop/emails/password_reset.txt",
        subject_template_name="shop/emails/password_reset_subject.txt",
        form_class=PasswordResetForm,
        success_url=reverse_lazy("shop:password-reset-done"),
    ), name="password-reset"),
    path("accounts/reset/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="shop/password_reset_done.html"), name="password-reset-done"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="shop/password_reset_confirm.html",
        form_class=SetPasswordForm,
        success_url=reverse_lazy("shop:password-reset-complete"),
    ), name="password-reset-confirm"),
    path("accounts/reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="shop/password_reset_complete.html"), name="password-reset-complete"),
]
