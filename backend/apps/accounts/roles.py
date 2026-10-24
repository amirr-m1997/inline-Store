"""Repeatable setup for the store's internal operating roles.

The groups use Django's native permissions, therefore they govern both the
admin menu and direct admin URLs.  Superusers remain untouched.
"""

from django.contrib.auth.models import Group, Permission


ROLE_DEFINITIONS = {
    "مدیر فروش": {
        "description": "سفارش‌ها، استعلام‌ها، مشتریان و قیمت‌گذاری سازمانی",
        "permissions": {
            "orders": ("order", "orderitem", "orderstatushistory", "payment", "invoice", "proformarequest"),
            "rfq": ("requestforquotation", "requestforquotationitem", "salesquotation", "salesquotationitem", "salesquotationresponse"),
            "pricing": ("productprice", "customerpricelist", "customerpricelistitem", "currencyrate"),
            "catalog": ("product", "category", "productbrand"),
            "accounts": ("user", "customeraddress", "view_management_reports"),
            "inventory": ("inventory",),
        },
        "modes": {"orders": "change", "rfq": "all", "pricing": "all", "catalog": "view", "accounts": "view", "inventory": "view"},
    },
    "انباردار": {
        "description": "موجودی، رسید و حواله، رزرو و نقطه سفارش",
        "permissions": {
            "inventory": ("inventory", "receipt", "issue", "reservation", "replenishmentrule"),
            "catalog": ("product", "category", "productdocument"),
            "orders": ("order", "orderitem"),
        },
        "modes": {"inventory": "all", "catalog": "view", "orders": "view"},
    },
    "مالی": {
        "description": "پرداخت، فاکتور، سفارش و گزارش‌های مدیریتی",
        "permissions": {
            "orders": ("order", "orderitem", "payment", "invoice", "invoiceemaillog", "proformarequest"),
            "pricing": ("productprice", "customerpricelist", "customerpricelistitem", "currencyrate"),
            "accounts": ("user", "view_management_reports"),
            "catalog": ("product",),
        },
        "modes": {"orders": "change", "pricing": "view", "accounts": "view", "catalog": "view"},
    },
    "محتوا": {
        "description": "کاتالوگ، رسانه، صفحات و محتوای منتشرشونده سایت",
        "permissions": {
            "catalog": (
                "product", "category", "productbrand", "productimage", "productdocument", "productidentifier",
                "attributedefinition", "categoryattribute", "productattributevalue", "supplybrand",
                "productreview", "productquestion",
            ),
            "company": "*",
            "content": "*",
            "website": ("footerlink", "footersection", "sitenavigation", "trustbadge"),
        },
        "modes": {"catalog": "all", "company": "all", "content": "all", "website": "all"},
    },
    "پشتیبانی": {
        "description": "رسیدگی به مشتری، پرسش‌ها، نظرات و درخواست‌های پشتیبانی",
        "permissions": {
            "accounts": ("user", "customeraddress"),
            "catalog": ("product", "productreview", "productquestion"),
            "orders": ("order", "orderitem"),
            "rfq": ("requestforquotation", "requestforquotationitem"),
            "website": ("customersupportrequest", "customerfeedback", "contactmessage", "warrantyregistration"),
        },
        "modes": {
            "accounts": "view", "orders": "view", "rfq": "change", "website": "change",
            # Support can moderate Q&A/reviews but cannot alter commercial
            # product data; products themselves stay read-only.
            "catalog": {"product": "view", "productreview": "change", "productquestion": "change"},
        },
    },
}


def _permission_codenames(model, mode):
    if model == "view_management_reports":
        return {"view_management_reports"}
    actions = ("add", "change", "delete", "view") if mode == "all" else ("view", "change") if mode == "change" else ("view",)
    return {f"{action}_{model}" for action in actions}


def ensure_internal_roles(*, verbosity=0):
    """Create or reconcile role groups without assigning any user to them."""
    results = []
    for role_name, config in ROLE_DEFINITIONS.items():
        wanted = set()
        for app_label, models in config["permissions"].items():
            configured_mode = config["modes"].get(app_label, "view")
            queryset = Permission.objects.filter(content_type__app_label=app_label)
            if models == "*":
                codenames = set()
                for permission in queryset:
                    if permission.codename.startswith(("add_", "change_", "delete_", "view_")):
                        codenames.add(permission.codename)
            else:
                codenames = set().union(*(
                    _permission_codenames(model, configured_mode.get(model, "view") if isinstance(configured_mode, dict) else configured_mode)
                    for model in models
                ))
            wanted.update(queryset.filter(codename__in=codenames))
        group, _ = Group.objects.get_or_create(name=role_name)
        group.permissions.set(wanted)
        results.append((role_name, len(wanted)))
    return results
