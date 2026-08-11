"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

export function CartButton() {
  const [count, setCount] = useState<number | null>(null);
  const load = useCallback(() => {
    const guestToken = localStorage.getItem("guestCartToken");
    const headers: Record<string, string> = {};
    if (guestToken) headers["X-Guest-Token"] = guestToken;
    fetch("/api/v1/cart/", { headers, cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((cart) => { if (cart) { if (cart.guest_token) localStorage.setItem("guestCartToken", cart.guest_token); setCount(cart.items.reduce((total: number, item: { quantity: number }) => total + item.quantity, 0)); } })
      .catch(() => setCount(null));
  }, []);
  useEffect(() => { load(); window.addEventListener("cart-updated", load); return () => window.removeEventListener("cart-updated", load); }, [load]);
  return <Link className="reference-cart" href="/fa/cart"><span className="cart-icon">🛒</span><span><b>سبد خرید</b><small>{count ? `${count.toLocaleString("fa-IR")} کالا` : "مشاهده سبد خرید"}</small></span><em>{count === null ? "—" : count.toLocaleString("fa-IR")}</em></Link>;
}
