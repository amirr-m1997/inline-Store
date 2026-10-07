"""سبد خرید فروشگاه مهراصل (سمت مشتری).

اصل طراحی: سبد هیچ قیمتی را ذخیره نمی‌کند — فقط شناسهٔ کالا و تعداد. هر بار که صفحه
رندر می‌شود، قیمت‌ها با `pricing.services.resolve_price` برای همان مشتری بازمحاسبه
می‌شود؛ بنابراین دست‌کاری قیمت از سمت مرورگر (تغییر input یا session) بی‌اثر است.
"""
from __future__ import annotations

import math

from django.conf import settings

from catalog.models import Product
from orders.services import prepare_lines

SESSION_KEY = "shop_cart"

# سقف تعداد هر ردیف سبد؛ از ورودی‌های بی‌معنا/سرریز عددی (که باعث خطای محاسباتی می‌شود)
# و از تحریف session جلوگیری می‌کند.
MAX_QTY = 1_000_000


def clean_qty(value) -> float:
    """تعداد ورودی را به عددی متناهی و در محدودهٔ مجاز تبدیل می‌کند."""
    try:
        qty = float(str(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
    except (TypeError, ValueError):
        raise ValueError("تعداد وارد‌شده معتبر نیست.")
    if not math.isfinite(qty):
        raise ValueError("تعداد وارد‌شده معتبر نیست.")
    if qty > MAX_QTY:
        raise ValueError(f"حداکثر تعداد مجاز در هر ردیف {MAX_QTY:,} است.")
    return qty


def safe_stored_qty(value) -> float:
    """تعداد ذخیره‌شده در session را در برابر مقادیر نامعتبر/سرریز مقاوم می‌کند."""
    try:
        qty = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(qty) or qty <= 0:
        return 0.0
    return min(qty, MAX_QTY)


class Cart:
    """سبد خرید مبتنی بر session برای مشتریان B2B."""

    def __init__(self, request):
        self.session = request.session
        data = self.session.get(SESSION_KEY)
        if not isinstance(data, dict) or "items" not in data:
            data = {"items": {}}
            self.session[SESSION_KEY] = data
        self.data = data

    # ------------------------------------------------------------------ عملیات
    def _save(self) -> None:
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, product: Product, qty: float = 1) -> float:
        key = str(product.pk)
        current = safe_stored_qty(self.data["items"].get(key, 0))
        new_qty = min(current + max(clean_qty(qty), 0), MAX_QTY)
        if new_qty <= 0:
            self.data["items"].pop(key, None)
        else:
            self.data["items"][key] = new_qty
        self._save()
        return new_qty

    def set_qty(self, product: Product, qty: float) -> None:
        key = str(product.pk)
        try:
            qty = clean_qty(qty)
        except ValueError:
            qty = 0
        if qty <= 0:
            self.data["items"].pop(key, None)
        else:
            self.data["items"][key] = qty
        self._save()

    def remove(self, product: Product) -> None:
        self.data["items"].pop(str(product.pk), None)
        self._save()

    def clear(self) -> None:
        self.data["items"] = {}
        self._save()

    # ------------------------------------------------------------------ وضعیت
    @property
    def is_empty(self) -> bool:
        return not self.data["items"]

    @property
    def count(self) -> int:
        """تعداد کل اقلام (جمع تعدادها) برای نشانگر سربرگ."""
        return int(min(sum(safe_stored_qty(q) for q in self.data["items"].values()), 10 ** 9))

    @property
    def distinct_count(self) -> int:
        return len(self.data["items"])

    def raw_items(self) -> list[tuple[str, float]]:
        """[(code, qty)] برای عبور از همان لایهٔ اعتبارسنجی/قیمت‌گذاری پنل."""
        ids = [int(pk) for pk in self.data["items"] if str(pk).isdigit()]
        products = {str(p.pk): p for p in Product.objects.filter(pk__in=ids, is_active=True)}
        rows = []
        for pk, qty in self.data["items"].items():
            product = products.get(str(pk))
            rows.append((product.code if product else str(pk), safe_stored_qty(qty)))
        return rows

    def rows(self, company=None) -> list[dict]:
        """ردیف‌های سبد با قیمت لحظه‌ای، وضعیت موجودی و پیام‌های قواعد فروش."""
        prepared = prepare_lines(company, self.raw_items())
        result = []
        for row in prepared:
            result.append({
                "product": row.product,
                "code": row.code,
                "qty": row.qty,
                "unit_price": row.unit_price,
                "list_price": row.list_price,
                "source": row.source,
                "discount_pct": row.discount_pct,
                "stock": row.stock or {},
                "notes": row.notes,
                "status": row.status,
                "key": row.key,
                "ok": row.ok,
                "total": row.line_total,
            })
        return result

    def totals(self, rows: list[dict]) -> dict:
        """جمع‌های سبد با احتساب ارزش افزوده و معافیت مشتری."""
        subtotal = sum(r["total"] for r in rows if r["ok"])
        list_total = sum(int(r["list_price"] * r["qty"]) for r in rows if r["ok"])
        vat_exempt = bool(getattr(self.company, "vat_exempt", False))
        vat = 0 if vat_exempt else int(round(subtotal * settings.VAT_RATE / 100))
        return {
            "subtotal": subtotal,
            "list_total": list_total,
            "discount": max(list_total - subtotal, 0),
            "vat": vat,
            "total": subtotal + vat,
            "blocked": [r for r in rows if not r["ok"]],
            "warnings": [r for r in rows if r["ok"] and r["status"] == "کمبود موجودی"],
        }


def membership_of(user):
    """عضویت سازمانی فعال کاربر (اگر وارد شده باشد)."""
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        user.company_membership
        if hasattr(user, "company_membership") and user.company_membership.is_active
        else None
    )


def cart_for(request) -> Cart:
    """سبد به‌همراه شرکت کاربر (برای قیمت‌گذاری اختصاصی) و عضویت او."""
    cart = Cart(request)
    membership = membership_of(getattr(request, "user", None))
    cart.membership = membership
    cart.company = membership.company if membership else None
    return cart
