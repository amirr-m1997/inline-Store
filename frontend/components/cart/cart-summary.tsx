import { formatNumber } from "../../lib/product/formatters";
type CartTotals = { subtotal: string; discount_amount: string; total: string; unpriced_items_count?: number; checkout_eligible?: boolean };
const money = (value: string | null | undefined) => value == null ? "—" : `${formatNumber(Number(value))} ریال`;
export function CartSummary({ cart }: { cart: CartTotals }) {
  const needsQuote = Boolean(cart.unpriced_items_count);
  return <section className="cart-summary" aria-labelledby="cart-summary-title"><h2 id="cart-summary-title">خلاصه سفارش</h2><dl className="cart-totals"><div><dt>{needsQuote ? "جمع اقلام قیمت‌دار" : "جمع کالاها"}</dt><dd>{money(cart.subtotal)}</dd></div>{Number(cart.discount_amount) > 0 && <div className="discount-row"><dt>تخفیف</dt><dd>− {money(cart.discount_amount)}</dd></div>}{needsQuote ? <div className="cart-quote-total" role="status"><dt>وضعیت پرداخت</dt><dd>نیازمند استعلام قیمت</dd></div> : <div className="grand-total"><dt>مبلغ قابل پرداخت</dt><dd>{money(cart.total)}</dd></div>}</dl>{needsQuote && <p className="cart-quote-note">{cart.unpriced_items_count} کالا قیمت قطعی ندارد؛ برای ثبت سفارش، ابتدا استعلام قیمت دریافت کنید.</p>}</section>;
}
