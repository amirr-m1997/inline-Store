"""زمینه‌های مشترک قالب‌های سایت مشتری."""
from __future__ import annotations


def shop_context(request):
    """تعداد اقلام سبد خرید و شرکت کاربر برای نشانگر سربرگ."""
    from .cart import membership_of, safe_stored_qty

    cart = request.session.get("shop_cart") if hasattr(request, "session") else None
    items = (cart or {}).get("items", {}) or {}
    count = int(sum(safe_stored_qty(q) for q in items.values())) if items else 0
    membership = membership_of(getattr(request, "user", None)) if getattr(request, "user", None) else None
    return {
        "cart_count": count,
        "header_membership": membership,
        "header_company": membership.company if membership else None,
    }
