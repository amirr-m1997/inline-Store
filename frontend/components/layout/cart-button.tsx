"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { FiShoppingCart } from "react-icons/fi";
import { getCart } from "../../lib/api/cart";
import { formatAccountNumber } from "../../lib/account-format";

export function CartButton({ locale = "fa" }: { locale?: string }) {
  const [count, setCount] = useState<number | null>(null);

  const load = useCallback(() => {
    getCart()
      .then((cart) => setCount(cart.items.reduce((total, item) => total + item.quantity, 0)))
      .catch(() => setCount(null));
  }, []);

  useEffect(() => {
    load();
    window.addEventListener("cart-updated", load);
    return () => window.removeEventListener("cart-updated", load);
  }, [load]);

  const label = count === null 
    ? "سبد خرید، وضعیت در حال دریافت" 
    : count 
      ? `سبد خرید، ${formatAccountNumber(count, locale)} کالا` 
      : "سبد خرید، خالی";

  const formattedCount = count === null ? "۰" : formatAccountNumber(count, locale);
  const dynamicStatus = count === null
    ? "در حال دریافت..."
    : count > 0
      ? `${formattedCount} کالا`
      : `${formattedCount} کالا | خالی`;

  return (
    <Link className="reference-cart" href={`/${locale}/cart`} aria-label={label}>
      <span className="cart-icon-box" aria-hidden="true">
        <FiShoppingCart size={19} className="cart-icon-svg" aria-hidden="true" />
        <em className="cart-badge-number">{formattedCount}</em>
      </span>
      <span className="cart-text-wrap">
        <b className="cart-title">سبد خرید</b>
        <small className="cart-status">{dynamicStatus}</small>
      </span>
    </Link>
  );
}
