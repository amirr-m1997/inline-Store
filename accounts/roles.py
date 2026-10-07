"""ماتریس نقش‌ها و دسترسی‌ها + همگام‌سازی گروه‌های جنگو."""
from __future__ import annotations

from django.contrib.auth.models import Group, Permission

# نگاشت نقش → (عنوان گروه، فهرست دسترسی‌های «app_label.codename»)
# "*" یعنی همه‌ی دسترسی‌های آن اپ.
ROLE_MATRIX: dict[str, dict] = {
    "sysadmin": {
        "group": "مدیر سیستم",
        "perms": ["*"],
    },
    "sales_manager": {
        "group": "مدیر فروش",
        "perms": [
            "catalog.view_product", "catalog.change_product", "catalog.approve_document",
            "pricing.view_pricelist", "pricing.change_pricelist",
            "pricing.view_pricelistitem", "pricing.change_pricelistitem",
            "pricing.view_quantitypricebreak", "pricing.change_quantitypricebreak",
            "customers.view_company", "customers.change_company",
            "customers.view_companyuser", "customers.view_companyaddress",
            "quotes.*", "orders.*", "inventory.view_stockitem", "inventory.view_stockmove",
            "finance.view_invoice", "finance.view_cheque", "core.view_auditlog",
        ],
    },
    "sales": {
        "group": "کارشناس فروش",
        "perms": [
            "catalog.view_product", "catalog.view_productdocument",
            "pricing.view_pricelist", "pricing.view_pricelistitem",
            "pricing.view_quantitypricebreak",
            "customers.view_company", "customers.view_companyuser",
            "quotes.view_quote", "quotes.add_quote", "quotes.change_quote",
            "quotes.view_quoteline", "quotes.add_quoteline", "quotes.change_quoteline",
            "quotes.view_quotemessage", "quotes.add_quotemessage",
            "orders.view_order", "orders.add_order", "orders.change_order",
            "orders.view_orderline", "orders.add_orderline", "orders.change_orderline",
            "orders.view_approval",
            "inventory.view_stockitem", "inventory.view_stockmove",
        ],
    },
    "warehouse": {
        "group": "انباردار",
        "perms": [
            "catalog.view_product",
            "inventory.*",
            "orders.view_order", "orders.view_orderline",
        ],
    },
    "finance": {
        "group": "مالی",
        "perms": [
            "finance.*",
            "customers.view_company", "customers.change_company",
            "orders.view_order", "orders.view_orderline", "orders.change_order",
            "orders.view_approval", "orders.change_approval",
            "quotes.view_quote",
            "inventory.view_stockitem",
            "core.view_auditlog",
        ],
    },
    "content": {
        "group": "محتوا",
        "perms": [
            "catalog.view_product", "catalog.add_product", "catalog.change_product",
            "catalog.add_productdocument", "catalog.change_productdocument",
            "catalog.view_productdocument", "catalog.view_category", "catalog.change_category",
            "catalog.view_brand", "catalog.view_spectemplate",
        ],
    },
    "support": {
        "group": "پشتیبانی فنی",
        "perms": [
            "catalog.view_product", "catalog.change_product", "catalog.add_productdocument",
            "catalog.change_productdocument", "catalog.view_productdocument",
            "catalog.view_productrelation", "catalog.add_productrelation",
            "quotes.view_quote", "quotes.change_quote", "quotes.view_quotemessage",
            "quotes.add_quotemessage",
            "orders.view_order", "orders.view_orderline", "inventory.view_stockitem",
        ],
    },
}

# قابلیت‌های اختصاصی (خارج از مدل‌ها) که در ماتریس گزارش آمده است
CUSTOM_PERMS: dict[str, list[str]] = {
    "sales_manager": ["approve_big_order", "approve_discount_over_limit", "assign_quote"],
    "sales": ["create_quote", "place_order_on_behalf"],
    "warehouse": ["adjust_stock", "stocktake"],
    "finance": ["approve_credit_exceed", "submit_to_moadian", "settle_cheque"],
    "sysadmin": ["impersonate_user", "view_full_audit"],
}


def _resolve(perms: list[str]) -> list[Permission]:
    resolved: list[Permission] = []
    for entry in perms:
        if entry == "*":
            resolved.extend(Permission.objects.all())
            continue
        if entry.endswith(".*"):
            app_label = entry[:-2]
            resolved.extend(Permission.objects.filter(content_type__app_label=app_label))
            continue
        app_label, codename = entry.split(".")
        resolved.extend(
            Permission.objects.filter(content_type__app_label=app_label, codename=codename)
        )
    return resolved


def sync_role_groups() -> dict[str, Group]:
    """ساخت/به‌روزرسانی گروه‌های نقش‌ها و دسترسی‌ها. خروجی: نگاشت نقش → گروه."""
    groups: dict[str, Group] = {}
    for role, definition in ROLE_MATRIX.items():
        group, _ = Group.objects.get_or_create(name=definition["group"])
        group.permissions.set(_resolve(definition["perms"]))
        groups[role] = group
    return groups


def ensure_profile(user):
    """اطمینان از وجود پروفایل برای کاربر."""
    from .models import Profile

    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def role_of(user) -> str:
    if not getattr(user, "is_authenticated", False):
        return "guest"
    if getattr(user, "is_superuser", False):
        return "sysadmin"
    profile = getattr(user, "profile", None)
    return profile.role if profile else "sales"
