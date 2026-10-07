"""سرویس سفارش: گردش تأیید، رزرو، ارسال، فاکتور."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core import audit
from core.models import AuditLog

from .models import Approval, ApprovalRule, Order, OrderEvent, OrderLine


def add_event(order: Order, title: str, description: str = "", kind: str = "note", actor=None):
    return OrderEvent.objects.create(
        order=order, title=title, description=description, kind=kind, actor=actor
    )


def evaluate_approvals(order: Order, actor=None) -> list[Approval]:
    """قواعد تأیید فعال را بررسی و مراحل لازم را ایجاد می‌کند."""
    order.approvals.filter(status="pending").delete()
    steps, created = [], []
    for rule in ApprovalRule.objects.filter(is_active=True).order_by("step", "threshold"):
        if rule.matches(order):
            steps.append(rule)
    if steps:
        order.status = "pending_approval"
        for index, rule in enumerate(steps, start=1):
            created.append(Approval.objects.create(
                order=order, rule=rule, step=index, required_role=rule.approver_role,
                amount_snapshot=order.net_amount,
            ))
        add_event(order, "نیازمند تأیید",
                  f"{len(created)} مرحله تأیید ایجاد شد (مبلغ: {order.net_amount:,} تومان)",
                  kind="approval", actor=actor)
    else:
        order.status = "approved"
        order.approved_at = timezone.now()
        add_event(order, "تأیید خودکار", "بدون نیاز به تأیید (در محدوده مجاز)", actor=actor)
    order.save(update_fields=["status", "approved_at"])
    return created


def approve(approval: Approval, user, comment: str = "") -> Order:
    """تأیید یک مرحله؛ در صورت تکمیل همه‌ی مراحل، سفارش تأییدشده می‌شود."""
    approval.status = "approved"
    approval.approver = user
    approval.acted_at = timezone.now()
    approval.comment = comment
    approval.save(update_fields=["status", "approver", "acted_at", "comment"])
    audit.log(action=AuditLog.Action.APPROVE, instance=approval, actor=user,
              note=f"تأیید سفارش {approval.order.number}", after={"status": "approved"})
    order = approval.order
    if not order.approvals.filter(status="pending").exists():
        order.status = "approved"
        order.approved_at = timezone.now()
        order.save(update_fields=["status", "approved_at"])
        add_event(order, "تأیید نهایی", f"توسط {user.get_full_name() or user.username}",
                  kind="approval", actor=user)
    return order


def reject(approval: Approval, user, reason: str = "") -> Order:
    approval.status = "rejected"
    approval.approver = user
    approval.acted_at = timezone.now()
    approval.comment = reason
    approval.save(update_fields=["status", "approver", "acted_at", "comment"])
    order = approval.order
    order.status = "draft"
    order.save(update_fields=["status"])
    add_event(order, "رد تأیید", reason or "بدون توضیح", kind="reject", actor=user)
    audit.log(action=AuditLog.Action.REJECT, instance=approval, actor=user,
              note=f"رد سفارش {order.number}: {reason}")
    return order


def reserve_stock(order: Order, user=None) -> Order:
    from inventory.services import reserve_for_order

    moves = reserve_for_order(order, user=user)
    order.status = "reserved"
    order.save(update_fields=["status"])
    add_event(order, "رزرو موجودی", f"{len(moves)} تراکنش رزرو ثبت شد", kind="stock", actor=user)
    return order


def mark_ready(order: Order, user=None) -> Order:
    order.status = "ready"
    order.save(update_fields=["status"])
    add_event(order, "آماده ارسال", actor=user)
    return order


def ship(order: Order, user=None, waybill: str = "", carrier: str = "", cost: int | None = None) -> Order:
    """ثبت ارسال: کسر فیزیکی از انبار و ثبت بارنامه."""
    from inventory.services import apply_move

    for line in order.lines.select_related("product", "warehouse"):
        remaining = float(line.remaining_to_ship)
        if remaining <= 0 or not line.warehouse:
            continue
        apply_move(product=line.product, warehouse=line.warehouse, kind="issue",
                   qty=remaining, reference=waybill or order.number, order=order, user=user,
                   note=f"ارسال سفارش {order.number}")
        if float(line.qty_reserved):
            apply_move(product=line.product, warehouse=line.warehouse, kind="release",
                       qty=line.qty_reserved, reference=order.number, order=order, user=user,
                       note=f"آزادسازی رزرو پس از ارسال {order.number}")
            line.qty_reserved = Decimal("0")
        line.qty_shipped = line.qty
        line.save(update_fields=["qty_shipped", "qty_reserved"])
    order.status = "shipped"
    order.shipped_at = timezone.now()
    if waybill:
        order.waybill_number = waybill
    if carrier:
        order.carrier_name = carrier
    if cost is not None:
        order.shipping_cost = cost
    order.save()
    add_event(order, "ارسال کالا", f"بارنامه {waybill or '—'} / {carrier or '—'}", kind="ship", actor=user)
    return order


def deliver(order: Order, user=None) -> Order:
    order.status = "delivered"
    order.delivered_at = timezone.now()
    order.save(update_fields=["status", "delivered_at"])
    add_event(order, "تحویل به مشتری", actor=user)
    return order


def cancel(order: Order, user=None, reason: str = "") -> Order:
    from inventory.services import release_for_order

    release_for_order(order, user=user)
    order.status = "cancelled"
    order.cancel_reason = reason
    order.save(update_fields=["status", "cancel_reason"])
    add_event(order, "لغو سفارش", reason, kind="cancel", actor=user)
    return order


@transaction.atomic
def create_invoice(order: Order, user=None, kind: str = "official"):
    """صدور فاکتور از سفارش."""
    from finance.models import Invoice, InvoiceLine

    invoice = Invoice.objects.create(
        kind=kind, order=order, company=order.company,
        subtotal=order.subtotal, discount_amount=order.discount_amount,
        shipping_amount=order.shipping_cost, total=order.total,
        vat_amount=order.vat,
        buyer_economic_code=order.company.economic_code,
        due_date=(timezone.localdate() + timezone.timedelta(days=order.company.credit_days or 0)),
        status="issued", created_by=user,
    )
    for line in order.lines.select_related("product"):
        InvoiceLine.objects.create(
            invoice=invoice, product=line.product,
            title=f"{line.product.name} ({line.product.code})",
            qty=line.qty, unit_price=line.unit_price, discount_pct=line.discount_pct,
        )
    add_event(order, "صدور فاکتور", invoice.number, kind="invoice", actor=user)
    return invoice


def order_timeline(order: Order):
    return order.events.select_related("actor").all()

# --------------------------------------------------------------- لایه‌ی مشترک ردیف‌ها
@dataclass
class LinePreview:
    """نتیجه‌ی اعتبارسنجی/قیمت‌گذاری یک ردیف پیش از ثبت سفارش.

    هم صفحه‌ی «سفارش سریع» پنل و هم فروشگاه مشتری از همین ساختار استفاده می‌کنند تا
    قواعد فروش (MOQ، مضرب بسته‌بندی، سبد قیمت، موجودی) فقط یک‌جا پیاده شده باشد.
    """

    code: str
    product: object | None
    qty: float
    list_price: int = 0
    unit_price: int = 0
    source: str = ""
    discount_pct: float = 0.0
    stock: dict | None = None
    notes: list[str] = field(default_factory=list)
    status: str = ""
    key: str = "muted"

    @property
    def ok(self) -> bool:
        return self.product is not None and self.key != "danger" and not self._hard_error

    @property
    def _hard_error(self) -> bool:
        return any(n.startswith("قواعد فروش") for n in self.notes)

    @property
    def line_total(self) -> int:
        return int(self.unit_price * self.qty)


def prepare_lines(company, raw_lines) -> list[LinePreview]:
    """ردیف‌های خام (کد/شناسه کالا، تعداد) را اعتبارسنجی و قیمت‌گذاری می‌کند.

    ترتیب کار برای هر ردیف: تشخیص کالا → گرد کردن به مضرب بسته‌بندی → بررسی MOQ/حداکثر →
    تعیین قیمت بر پایه‌ی سبد قیمت مشتری و پله‌های حجمی → بررسی موجودی آزاد.
    """
    from catalog.models import Product
    from inventory.services import stock_check
    from pricing.services import resolve_price

    prepared: list[LinePreview] = []
    for code, qty in raw_lines:
        product = None
        if code:
            product = (
                Product.objects.filter(code__iexact=str(code).strip()).first()
                or Product.objects.filter(name__iexact=str(code).strip()).first()
            )
        row = LinePreview(code=str(code or "—"), product=product, qty=float(qty or 0))
        if product is None:
            row.status, row.key = "کد ناشناس", "danger"
            row.notes.append("کالایی با این کد یافت نشد.")
            prepared.append(row)
            continue
        if row.qty <= 0:
            row.status, row.key = "تعداد نامعتبر", "danger"
            row.notes.append("تعداد باید بزرگ‌تر از صفر باشد.")
            prepared.append(row)
            continue

        packed = float(product.apply_packaging(row.qty))
        if packed != row.qty:
            row.notes.append(f"مضرب بسته‌بندی: {packed:g} (تعداد درخواستی {row.qty:g})")
            row.qty = packed
        error = product.validate_qty(row.qty)
        if error:
            row.status, row.key = "خارج از قواعد فروش", "warn"
            row.notes.append(f"قواعد فروش: {error}")
            prepared.append(row)
            continue

        price = resolve_price(product, company=company, qty=row.qty)
        stock = stock_check(product, row.qty)
        row.list_price = price.list_price
        row.unit_price = price.unit_price
        row.source = price.source
        row.discount_pct = price.total_discount_pct
        row.stock = stock
        if not stock["sufficient"]:
            row.status, row.key = "کمبود موجودی", "warn"
            row.notes.append(
                f"موجودی آزاد {stock['free']:g} — کسری {stock['shortage']:g} "
                f"(تأمین {product.lead_time_days} روز)"
            )
        else:
            row.status, row.key = "یافته شد", "ok"
        prepared.append(row)
    return prepared


@transaction.atomic
def create_order(*, company, rows, actor=None, po_number: str = "", project_name: str = "",
                 customer_note: str = "", placed_by_rep: bool = False, shipping_address=None,
                 shipping_method: str = "pickup", payment_method: str | None = None,
                 contact=None) -> Order:
    """ساخت سفارش از ردیف‌های اعتبارسنجی‌شده + قرار دادن در گردش تأیید."""
    bookable = [row for row in rows if row.ok and row.unit_price >= 0]
    if not bookable:
        raise ValueError("هیچ ردیف قابل ثبتی وجود ندارد.")

    order = Order.objects.create(
        company=company,
        contact=contact,
        po_number=po_number,
        project_name=project_name,
        sales_rep=company.sales_rep,
        created_by=actor,
        payment_method=payment_method or ("cheque" if company.payment_terms == "cheque" else "credit"),
        payment_terms=company.get_payment_terms_display(),
        shipping_method=shipping_method,
        shipping_address=shipping_address,
        placed_by_rep_for_company=placed_by_rep,
        customer_note=customer_note,
    )
    for row in bookable:
        warehouse = (row.stock or {}).get("warehouse")
        OrderLine.objects.create(
            order=order, product=row.product, qty=row.qty, unit_price=row.unit_price,
            list_price=row.list_price or row.product.base_price, warehouse=warehouse,
            lead_time_days=row.product.lead_time_days,
        )
    evaluate_approvals(order, actor=actor)
    add_event(order, "ثبت سفارش", f"{len(bookable)} قلم کالا", actor=actor)
    return order
