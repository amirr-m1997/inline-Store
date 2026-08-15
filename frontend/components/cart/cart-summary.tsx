type CartTotals = { subtotal: string; discount_amount: string; total: string };
const money = (value: string | null | undefined) => value == null ? "—" : `${Number(value).toLocaleString("fa-IR")} ریال`;
export function CartSummary({ cart }: { cart: CartTotals }) {
  return <section className="cart-summary" aria-labelledby="cart-summary-title"><h2 id="cart-summary-title">خلاصه سفارش</h2><dl className="cart-totals"><div><dt>جمع کالاها</dt><dd>{money(cart.subtotal)}</dd></div>{Number(cart.discount_amount) > 0 && <div className="discount-row"><dt>تخفیف</dt><dd>− {money(cart.discount_amount)}</dd></div>}<div className="grand-total"><dt>مبلغ قابل پرداخت</dt><dd>{money(cart.total)}</dd></div></dl></section>;
}
