"""تولید اعلان‌های خودکار: موجودی کم، SLA استعلام، سفارش معطل، چک سررسید، قیمت در آستانه انقضا."""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from core.models import Notification
from customers.models import Company
from finance.models import Cheque
from inventory.models import StockItem
from orders.models import Approval
from pricing.models import PriceList
from quotes.models import Quote


class Command(BaseCommand):
    help = "بررسی وضعیت سیستم و ساخت اعلان‌های هشدار (بدون تکرار)"

    def add_arguments(self, parser):
        parser.add_argument("--quiet", action="store_true")

    def handle(self, *args, **options):
        created = 0
        created += self._low_stock()
        created += self._rfq_sla()
        created += self._pending_approvals()
        created += self._cheques()
        created += self._price_expiry()
        created += self._credit_exceed()
        if not options["quiet"]:
            self.stdout.write(self.style.SUCCESS(f"{created} اعلان جدید ساخته شد."))

    # ------------------------------------------------------------- helpers
    def _create(self, **kwargs):
        dedup = kwargs.pop("dedup_key", None)
        if dedup and Notification.objects.filter(dedup_key=dedup).exists():
            return 0
        Notification.objects.create(dedup_key=dedup, **kwargs)
        return 1

    def _low_stock(self):
        count = 0
        for item in StockItem.objects.select_related("product", "warehouse"):
            key, label, _ = item.status
            if key not in ("critical", "low", "out", "error"):
                continue
            count += self._create(
                kind="low_stock", level="danger" if key in ("critical", "out", "error") else "warning",
                title=f"موجودی کم: {item.product.name}",
                body=f"{item.warehouse.name} — موجودی آزاد {item.free_qty} {item.product.get_uom_display()} "
                     f"(نقطه سفارش {item.reorder_point})",
                url=f"/admin/inventory/stockitem/{item.pk}/change/",
                dedup_key=f"low_stock:{item.pk}:{timezone.localdate()}",
            )
        return count

    def _rfq_sla(self):
        count = 0
        overdue = Quote.objects.filter(
            status__in=["new", "tech_review", "pricing", "sent", "negotiation"],
            sla_due_at__lt=timezone.now(),
        ).select_related("company", "assigned_to")
        for quote in overdue:
            count += self._create(
                kind="rfq_sla", level="danger",
                title=f"استعلام {quote.number} از SLA عبور کرد",
                body=f"{quote.company.name} — کارشناس: "
                     f"{(quote.assigned_to.get_full_name() if quote.assigned_to else 'تخصیص نیافته')}",
                url=f"/admin/quotes/quote/{quote.pk}/change/",
                company=quote.company,
                dedup_key=f"rfq_sla:{quote.pk}:{quote.sla_due_at:%Y%m%d%H}",
            )
        return count

    ROLE_LABELS = {"sales_manager": "مدیر فروش", "finance": "مدیر مالی", "sysadmin": "مدیر سیستم"}

    def _pending_approvals(self):
        count = 0
        for approval in Approval.objects.filter(status="pending").select_related("order__company"):
            count += self._create(
                kind="order_pending", level="warning",
                title=f"سفارش {approval.order.number} در انتظار تأیید",
                body=f"{approval.order.company.name} — مرحله {approval.step} "
                     f"({self.ROLE_LABELS.get(approval.required_role, approval.required_role)}) — مبلغ {approval.amount_snapshot:,} تومان",
                url=f"/admin/orders/approval/{approval.pk}/change/",
                company=approval.order.company,
                dedup_key=f"order_pending:{approval.pk}",
            )
        return count

    def _cheques(self):
        count = 0
        today = timezone.localdate()
        cheques = Cheque.objects.filter(status__in=["in_hand", "deposited"],
                                        due_date__lte=today + timedelta(days=7)).select_related("company")
        for cheque in cheques:
            days = cheque.days_to_due
            level = "danger" if days <= 2 else "warning"
            count += self._create(
                kind="cheque_due", level=level,
                title=f"چک {cheque.number} — {cheque.company.name}",
                body=f"سررسید {cheque.due_date} ({'معوق' if days < 0 else f'{days} روز دیگر'}) — "
                     f"مبلغ {cheque.amount:,} تومان — بانک {cheque.bank}",
                url=f"/admin/finance/cheque/{cheque.pk}/change/",
                company=cheque.company,
                dedup_key=f"cheque:{cheque.pk}:{cheque.due_date}",
            )
        return count

    def _price_expiry(self):
        count = 0
        today = timezone.localdate()
        for price_list in PriceList.objects.filter(is_active=True, valid_until__isnull=False):
            days = (price_list.valid_until - today).days
            if days > 14:
                continue
            level = "danger" if days < 0 else "warning"
            count += self._create(
                kind="price_expiring", level=level,
                title=f"سبد قیمت «{price_list.name}» {'منقضی شده' if days < 0 else f'{days} روز تا انقضا'}",
                body=f"{price_list.items.count()} قلم قیمت اختصاصی — نیازمند بازنگری",
                url=f"/admin/pricing/pricelist/{price_list.pk}/change/",
                dedup_key=f"price_expiry:{price_list.pk}:{price_list.valid_until}",
            )
        return count

    def _credit_exceed(self):
        count = 0
        for company in Company.objects.filter(is_active=True, credit_limit__gt=0):
            if company.credit_usage_pct >= 90:
                count += self._create(
                    kind="credit_exceed", level="danger" if company.credit_usage_pct >= 100 else "warning",
                    title=f"مصرف اعتبار {company.name}: {company.credit_usage_pct}%",
                    body=f"مصرف {company.credit_used:,} از سقف {company.credit_limit:,} تومان",
                    url=f"/admin/customers/company/{company.pk}/change/",
                    company=company,
                    dedup_key=f"credit:{company.pk}:{timezone.localdate()}",
                )
        return count
