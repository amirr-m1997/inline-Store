"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const storageKey = "productCompareSlugs";

export function ProductCompareTray({ locale }: { locale: string }) {
  const [slugs, setSlugs] = useState<string[]>([]);
  useEffect(() => {
    const load = () => setSlugs(JSON.parse(window.localStorage.getItem(storageKey) || "[]"));
    const update = (event: Event) => setSlugs((event as CustomEvent<string[]>).detail || []);
    load(); window.addEventListener("product-compare-updated", update); window.addEventListener("storage", load);
    return () => { window.removeEventListener("product-compare-updated", update); window.removeEventListener("storage", load); };
  }, []);
  if (!slugs.length) return null;
  const clear = () => { window.localStorage.removeItem(storageKey); setSlugs([]); window.dispatchEvent(new CustomEvent("product-compare-updated", { detail: [] })); };
  return <aside className="product-compare-tray" aria-label="محصولات انتخاب‌شده برای مقایسه"><span>{slugs.length.toLocaleString("fa-IR")} محصول برای مقایسه انتخاب شده</span><Link href={`/${locale}/compare`}>مقایسه محصولات ←</Link><button type="button" onClick={clear}>پاک کردن</button></aside>;
}
