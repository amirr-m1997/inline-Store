"""نمایش‌های سایت مشتری مهراصل: کاتالوگ، سبد خرید، ثبت سفارش، پرداخت و حساب کاربری.

قواعد امنیتی رعایت‌شده در این لایه:
- هیچ قیمتی از ورودی کاربر پذیرفته نمی‌شود؛ همه‌ی مبالغ سمت سرور از سبد قیمت مشتری بازمحاسبه می‌شود.
- دسترسی به سفارش/فاکتور همیشه با فیلتر «شرکت کاربر» محدود می‌شود (جلوگیری از IDOR).
- عملیات تغییردهنده فقط با POST و CSRF انجام می‌شود.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalog.models import Brand, Category, Product
from core.utils import fa, jalali, money, num
from customers.models import CompanyAddress, CompanyUser
from finance.models import Invoice
from finance.services import register_payment
from inventory.services import stock_check
from orders.models import Order
from orders.services import create_order
from pricing.services import price_levels_for, resolve_price
from quotes.models import Quote, QuoteLine

from . import forms as shop_forms
from .cart import cart_for, clean_qty, membership_of

# ------------------------------------------------------------------ کمکی‌ها


def _company_gate(user):
    """(company, error) — بررسی شرایط لازم برای ثبت سفارش سازمانی."""
    membership = membership_of(user)
    if membership is None:
        return None, "حساب کاربری شما به هیچ حساب سازمانی فعالی متصل نیست. با پشتیبانی تماس بگیرید."
    company = membership.company
    if not company.is_active:
        return company, "حساب سازمانی شما غیرفعال است؛ با کارشناس فروش تماس بگیرید."
    if company.is_blacklisted:
        return company, "امکان ثبت سفارش برای این حساب وجود ندارد؛ با واحد فروش تماس بگیرید."
    if company.kyc_status != "approved":
        return company, ("حساب سازمانی شما در انتظار بررسی و تأیید (KYC) است. "
                         "می‌توانید کالاها را انتخاب کنید و سبد را به‌عنوان «درخواست قیمت» برای کارشناس فروش بفرستید.")
    return company, None


def _require_invoice_access(request, membership, company):
    """آیا این کاربر اجازهٔ دیدن فاکتورهای شرکت را دارد؟"""
    if membership.can_view_invoices or membership.role in ("admin", "approver", "finance") or request.user.is_staff:
        return True
    return False


# ------------------------------------------------------------------ کاتالوگ
def home(request):
    """صفحهٔ اصلی: جست‌وجو، فیلتر دسته/برند، مرتب‌سازی و صفحه‌بندی کالاها."""
    cart = cart_for(request)
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .prefetch_related("images", "stock_items")
    )
    q = (request.GET.get("q") or "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(code__icontains=q) | Q(name_en__icontains=q)
            | Q(model_number__icontains=q) | Q(tags__icontains=q)
        )
    category_slug = request.GET.get("cat") or ""
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()
        if category:
            children = list(category.children.values_list("slug", flat=True)) if hasattr(category, "children") else []
            products = products.filter(Q(category=category) | Q(category__slug__in=children))
    brand_id = request.GET.get("brand") or ""
    if brand_id.isdigit():
        products = products.filter(brand_id=brand_id)
    availability = request.GET.get("avail") or ""
    if availability:
        products = products.filter(availability=availability)

    sort = request.GET.get("sort") or "new"
    ordering = {
        "new": "-created_at",
        "cheap": "base_price",
        "expensive": "-base_price",
        "name": "name",
    }.get(sort, "-created_at")
    products = products.order_by(ordering)

    paginator = Paginator(products, 12)
    page = paginator.get_page(request.GET.get("page"))

    categories = (
        Category.objects.filter(is_active=True)
        .annotate(products_count=Count("products", filter=Q(products__is_active=True)))
        .order_by("order", "name")
    )
    context = {
        "page_obj": page,
        "products": page.object_list,
        "prices": _card_prices(page.object_list, cart.company),
        "categories": categories,
        "brands": Brand.objects.filter(is_active=True).order_by("name"),
        "q": q,
        "selected_category": category_slug,
        "selected_brand": brand_id,
        "selected_availability": availability,
        "sort": sort,
        "total_count": paginator.count,
        "cart": cart,
        "hero_stats": {
            "products": Product.objects.filter(is_active=True).count(),
            "categories": Category.objects.filter(is_active=True).count(),
            "brands": Brand.objects.filter(is_active=True).count(),
        },
    }
    return render(request, "shop/home.html", context)


def _card_prices(products, company):
    """قیمت نمایشی هر کالا در فهرست (با احتساب سبد قیمت مشتری)."""
    prices = {}
    for product in products:
        result = resolve_price(product, company=company, qty=max(float(product.min_order_qty or 1), 1))
        prices[product.pk] = {
            "unit_price": result.unit_price,
            "discount_pct": result.total_discount_pct,
            "source": result.source,
        }
    return prices


def product_detail(request, slug):
    cart = cart_for(request)
    product = get_object_or_404(
        Product.objects.select_related("category", "brand", "spec_template").prefetch_related("images", "documents"),
        slug=slug, is_active=True,
    )
    qty = float(request.GET.get("qty") or product.min_order_qty or 1)
    price = resolve_price(product, company=cart.company, qty=qty)
    stock = stock_check(product, qty)
    related = list(
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)
        .select_related("brand")
        .prefetch_related("images", "stock_items")[:4]
    )
    rows = [
        {
            "product": product,
            "qty": qty,
            "unit_price": price.unit_price,
            "list_price": price.list_price,
            "source": price.source,
            "discount_pct": price.total_discount_pct,
            "stock": stock,
            "notes": [],
            "status": "یافته شد" if stock["sufficient"] else "کمبود موجودی",
            "key": "ok" if stock["sufficient"] else "warn",
            "ok": True,
            "total": int(price.unit_price * qty),
        }
    ]
    context = {
        "product": product,
        "cart": cart,
        "price": price,
        "stock": stock,
        "qty": qty,
        "totals": cart.totals(rows),
        "levels": price_levels_for(product, company=cart.company),
        "related": related,
        "related_prices": _card_prices(related, cart.company),
        "specs": (product.specs or {}).items(),
    }
    return render(request, "shop/product.html", context)


# ------------------------------------------------------------------ سبد خرید
def cart_view(request):
    cart = cart_for(request)
    rows = cart.rows(cart.company)
    totals = cart.totals(rows)
    company, gate_error = (None, None)
    if request.user.is_authenticated:
        company, gate_error = _company_gate(request.user)
    return render(request, "shop/cart.html", {
        "cart": cart, "rows": rows, "totals": totals,
        "company": company, "gate_error": gate_error,
    })


@require_POST
def cart_add(request, pk):
    cart = cart_for(request)
    product = get_object_or_404(Product, pk=pk, is_active=True)
    try:
        qty = clean_qty(request.POST.get("qty") or "1")
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("shop:product", slug=product.slug)
    if qty <= 0:
        messages.error(request, "تعداد باید بزرگ‌تر از صفر باشد.")
        return redirect("shop:product", slug=product.slug)
    new_qty = cart.add(product, qty)
    messages.success(request, f"«{product.name}» به سبد خرید اضافه شد (تعداد کل: {num(new_qty, 0)}).")
    target = request.POST.get("next") or ""
    if target == "cart":
        return redirect("shop:cart")
    # مقصد بازگشت فقط می‌تواند مسیری داخلیِ همین دامنه باشد
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                require_https=request.is_secure()):
        return redirect(target)
    return redirect("shop:home")


@require_POST
def cart_update(request, pk):
    cart = cart_for(request)
    product = get_object_or_404(Product, pk=pk, is_active=True)
    action = request.POST.get("action") or "set"
    if action == "remove":
        cart.remove(product)
        messages.info(request, f"«{product.name}» از سبد حذف شد.")
    else:
        try:
            qty = clean_qty(request.POST.get("qty") or "0")
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("shop:cart")
        cart.set_qty(product, qty)
        messages.success(request, "سبد خرید به‌روزرسانی شد.")
    return redirect("shop:cart")


@require_POST
def cart_clear(request):
    cart_for(request).clear()
    messages.info(request, "سبد خرید خالی شد.")
    return redirect("shop:cart")


# ------------------------------------------------------------------ ثبت سفارش
@login_required
def checkout(request):
    cart = cart_for(request)
    company, gate_error = _company_gate(request.user)
    rows = cart.rows(company or None)
    totals = cart.totals(rows)

    if not rows:
        messages.info(request, "سبد خرید شما خالی است.")
        return redirect("shop:home")

    membership = membership_of(request.user)
    form = shop_forms.CheckoutForm(request.POST or None, company=company, user=request.user)

    credit = None
    if company is not None and company.credit_limit:
        credit = {
            "used": company.credit_used,
            "limit": company.credit_limit,
            "available": company.credit_available,
            "pct": company.credit_usage_pct,
            "status": company.credit_status,
        }
    over_limit = bool(credit and totals["total"] > credit["available"])

    if request.method == "POST" and gate_error is None and form.is_valid():
        needs_credit = form.cleaned_data["payment_method"] in ("credit", "cheque")
        if needs_credit and over_limit:
            messages.error(
                request,
                "مبلغ سفارش از اعتبار باقی‌ماندهٔ شما بیشتر است؛ پرداخت آنلاین را انتخاب کنید "
                "یا سبد را به‌عنوان درخواست قیمت برای کارشناس فروش بفرستید.",
            )
        else:
            order = create_order(
                company=company,
                rows=[_row_object(r) for r in rows if r["ok"]],
                actor=request.user,
                po_number=form.cleaned_data["po_number"],
                project_name=form.cleaned_data["project_name"],
                customer_note=form.cleaned_data["customer_note"],
                contact=membership,
                shipping_address=form.save_address(),
                shipping_method="pickup" if form.cleaned_data["shipping_method"] == "pickup" else "freight",
                payment_method="gateway" if form.cleaned_data["payment_method"] == "online"
                else ("cheque" if form.cleaned_data["payment_method"] == "cheque" else "credit"),
            )
            invoice = _issue_invoice(order, request.user)
            cart.clear()
            messages.success(request, f"سفارش {order.number} با موفقیت ثبت شد.")
            if form.cleaned_data["payment_method"] == "online":
                return redirect("shop:invoice-pay", number=invoice.number)
            return redirect("shop:order-detail", number=order.number)

    return render(request, "shop/checkout.html", {
        "cart": cart, "rows": rows, "totals": totals, "form": form,
        "company": company, "company_error": gate_error, "credit": credit,
        "over_limit": over_limit, "membership": membership,
    })


class _Row:
    """تبدیل dict ردیف سبد به شکل مورد انتظار create_order."""

    def __init__(self, data):
        self.product = data["product"]
        self.qty = data["qty"]
        self.unit_price = data["unit_price"]
        self.list_price = data["list_price"]
        self.stock = data["stock"]
        self.ok = data["ok"]
        self.code = data["code"]


def _row_object(data) -> _Row:
    return _Row(data)


def _issue_invoice(order, user):
    from orders.services import create_invoice

    return create_invoice(order, user=user, kind="proforma")


@require_POST
@login_required
def rfq_from_cart(request):
    """ارسال سبد خرید به‌عنوان درخواست قیمت (RFQ) برای کارشناس فروش."""
    cart = cart_for(request)
    company, gate_error = _company_gate(request.user)
    rows = cart.rows(company or None)
    bookable = [r for r in rows if r["product"]]
    if not bookable:
        messages.error(request, "برای ثبت درخواست قیمت، حداقل یک کالا لازم است.")
        return redirect("shop:cart")
    if gate_error and (company is None or not company.is_active):
        messages.error(request, gate_error)
        return redirect("shop:cart")

    membership = membership_of(request.user)
    quote = Quote.objects.create(
        company=company, contact=membership,
        project_name=(request.POST.get("project_name") or "")[:160],
        priority="normal", source="site",
        customer_note=(request.POST.get("note") or "درخواست قیمت از سبد خرید سایت")[:2000],
        assigned_to=company.sales_rep, created_by=request.user,
        status="new",
    )
    for row in bookable:
        QuoteLine.objects.create(
            quote=quote, product=row["product"], qty=row["qty"],
            list_price=row["list_price"], offered_price=row["unit_price"],
            discount_pct=row["discount_pct"], lead_time_days=row["product"].lead_time_days,
        )
    cart.clear()
    messages.success(request, f"درخواست قیمت {quote.number} ثبت شد؛ کارشناس فروش پاسخ می‌دهد.")
    return redirect("shop:orders")


# ------------------------------------------------------------------ سفارش‌ها و فاکتورها
@login_required
def order_list(request):
    membership = membership_of(request.user)
    if membership is None:
        messages.error(request, "حساب کاربری شما به هیچ حساب سازمانی متصل نیست.")
        return redirect("shop:home")
    orders = (
        Order.objects.filter(company=membership.company)
        .select_related("company", "shipping_address")
        .prefetch_related("lines__product")
        .order_by("-ordered_at")
    )
    invoices = (
        Invoice.objects.filter(company=membership.company)
        .select_related("order")
        .order_by("-issued_at", "-id")[:50]
    ) if _require_invoice_access(request, membership, membership.company) else Invoice.objects.none()
    return render(request, "shop/order_list.html", {
        "membership": membership, "orders": orders[:60], "invoices": invoices,
        "can_view_invoices": _require_invoice_access(request, membership, membership.company),
    })


def _owned_order(request, number):
    membership = membership_of(request.user)
    if membership is None:
        return None, None
    order = get_object_or_404(
        Order.objects.select_related("company", "shipping_address").prefetch_related("lines__product", "events"),
        number=number, company=membership.company,
    )
    return order, membership


@login_required
def order_detail(request, number):
    order, membership = _owned_order(request, number)
    if order is None:
        messages.error(request, "سفارش یافت نشد.")
        return redirect("shop:home")
    invoices = order.invoices.all() if hasattr(order, "invoices") else Invoice.objects.filter(order=order)
    return render(request, "shop/order_detail.html", {
        "order": order, "membership": membership, "invoices": invoices,
        "can_pay": any(inv.balance > 0 for inv in invoices),
    })


@login_required
def invoice_detail(request, number):
    membership = membership_of(request.user)
    if membership is None:
        return redirect("shop:home")
    if not _require_invoice_access(request, membership, membership.company):
        messages.error(request, "دسترسی به فاکتورها برای نقش شما فعال نیست؛ با مدیر حساب تماس بگیرید.")
        return redirect("shop:orders")
    invoice = get_object_or_404(
        Invoice.objects.select_related("company", "order").prefetch_related("lines__product"),
        number=number, company=membership.company,
    )
    return render(request, "shop/invoice.html", {"invoice": invoice, "membership": membership})


# ------------------------------------------------------------------ پرداخت (درگاه آزمایشی)
@login_required
def invoice_pay(request, number):
    membership = membership_of(request.user)
    if membership is None:
        return redirect("shop:home")
    if not _require_invoice_access(request, membership, membership.company):
        messages.error(request, "پرداخت فاکتور نیازمند دسترسی مالی است.")
        return redirect("shop:orders")
    invoice = get_object_or_404(
        Invoice.objects.select_related("company").filter(company=membership.company), number=number,
    )
    if invoice.balance <= 0:
        messages.info(request, "این فاکتور قبلاً تسویه شده است.")
        return redirect("shop:invoice", number=invoice.number)

    form = shop_forms.PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payment = register_payment(
            company=invoice.company, amount=invoice.balance, method="gateway",
            invoice=invoice, order=invoice.order,
            reference=f"MOCK-{uuid.uuid4().hex[:12].upper()}",
            bank=form.cleaned_data["gateway"], user=request.user,
        )
        invoice.refresh_from_db()
        messages.success(
            request,
            f"پرداخت {money(payment.amount)} با شمارهٔ پیگیری {payment.reference} ثبت شد. "
            f"وضعیت فاکتور: {invoice.get_status_display()}.",
        )
        return redirect("shop:payment-success", number=invoice.number)
    return render(request, "shop/payment_gateway.html", {
        "invoice": invoice, "form": form, "membership": membership,
    })


@login_required
def payment_success(request, number):
    membership = membership_of(request.user)
    invoice = get_object_or_404(Invoice.objects.filter(company=membership.company) if membership else Invoice.objects.none(),
                                number=number)
    return render(request, "shop/payment_success.html", {"invoice": invoice, "membership": membership})


# ------------------------------------------------------------------ حساب کاربری
def signup(request):
    if request.user.is_authenticated:
        return redirect("shop:home")
    form = shop_forms.SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(
            request,
            "ثبت‌نام انجام شد. حساب سازمانی شما برای تأیید به کارشناس فروش ارجاع شد؛ "
            "تا آن زمان می‌توانید کالاها را ببینید و درخواست قیمت ثبت کنید.",
        )
        return redirect("shop:home")
    return render(request, "shop/signup.html", {"form": form})


@require_POST
def logout_view(request):
    """خروج فقط با POST (فرم سربرگ) تا با یک لینک/تصویر بیرونی قابل اجبار نباشد."""
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, "از حساب کاربری خارج شدید.")
    return redirect("shop:home")


@login_required
def profile(request):
    membership = membership_of(request.user)
    form = shop_forms.ProfileForm(request.POST or None, user=request.user, membership=membership)
    address_form = shop_forms.AddressForm(request.POST or None, prefix="addr")
    if request.method == "POST":
        if "submit-profile" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "اطلاعات حساب به‌روزرسانی شد.")
            return redirect("shop:profile")
        if "submit-address" in request.POST and address_form.is_valid() and membership is not None:
            address = address_form.save(commit=False)
            address.company = membership.company
            if address.is_default:
                membership.company.addresses.update(is_default=False)
            address.save()
            messages.success(request, "نشانی جدید ثبت شد.")
            return redirect("shop:profile")
    return render(request, "shop/profile.html", {
        "form": form, "address_form": address_form, "membership": membership,
        "addresses": membership.company.addresses.all() if membership else [],
        "orders_count": Order.objects.filter(company=membership.company).count() if membership else 0,
    })


@require_POST
@login_required
def address_delete(request, pk):
    membership = membership_of(request.user)
    if membership is None:
        return redirect("shop:home")
    address = get_object_or_404(CompanyAddress, pk=pk, company=membership.company)
    if address.is_default and membership.company.addresses.count() > 1:
        messages.error(request, "نشانی پیش‌فرض را نمی‌توان حذف کرد؛ ابتدا نشانی دیگری را پیش‌فرض کنید.")
    else:
        address.delete()
        messages.info(request, "نشانی حذف شد.")
    return redirect("shop:profile")


# ------------------------------------------------------------------ صفحه‌های اطلاعی
def about(request):
    return render(request, "shop/about.html", {"cart": cart_for(request)})


def contact(request):
    return render(request, "shop/contact.html", {"cart": cart_for(request)})
