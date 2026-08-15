"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getCart } from "../../lib/api/cart";
import { formatAccountNumber } from "../../lib/account-format";

export function CartButton({ locale = "fa" }: { locale?: string }) {
  const [count, setCount] = useState<number | null>(null);
  const load = useCallback(() => {
    getCart()
      .then((cart) => setCount(cart.items.reduce((total, item) => total + item.quantity, 0)))
      .catch(() => setCount(null));
  }, []);
  useEffect(() => { load(); window.addEventListener("cart-updated", load); return () => window.removeEventListener("cart-updated", load); }, [load]);
  const label = count === null ? "سبد خرید، وضعیت در حال دریافت" : count ? `سبد خرید، ${formatAccountNumber(count, locale)} کالا` : "سبد خرید، خالی";
  return <Link className="reference-cart" href={`/${locale}/cart`} aria-label={label}><span className="cart-icon" aria-hidden="true">🛒</span><span><b>سبد خرید</b><small>{count ? `${formatAccountNumber(count, locale)} کالا` : "مشاهده سبد خرید"}</small></span><em aria-hidden="true">{count === null ? "—" : formatAccountNumber(count, locale)}</em></Link>;
}
