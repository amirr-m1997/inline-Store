"use client";

import { useState } from "react";
import { ProductCard as DomainProductCard } from "../product/product-card/product-card";
import { Skeleton } from "../ui/skeleton";
import { toProductSummary } from "../../lib/product/adapters";
import { ApiError, apiRequest } from "../../lib/api/client";

export type CatalogProduct = {
  id: number;
  name: string;
  slug: string;
  code: string;
  unit: string;
  available_quantity: number | null;
  short_description?: string | null;
  category: { name_fa: string } | null;
  images: { image: string; alt_text: string; alt_fa?: string; is_primary?: boolean }[];
  price: { original_amount: string; final_amount: string; discount_percentage: string } | null;
};

export function ProductCard({ product, priority = false, locale = "fa" }: { product: CatalogProduct; priority?: boolean; locale?: string }) {
  return <div className="catalog-product-card-wrap"><ProductCardActions product={product} locale={locale} /><DomainProductCard product={toProductSummary(product)} priority={priority} locale={locale} /></div>;
}

function ProductCardActions({ product, locale }: { product: CatalogProduct; locale: string }) {
  const [favorited, setFavorited] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [checked, setChecked] = useState(false);
  const english = locale === "en";
  const endpoint = `/api/v1/catalog/products/${product.id}/favorite/`;
  const ensureFavoriteState = async () => {
    if (checked) return;
    setChecked(true);
    try {
      const response = await apiRequest<{ is_favorited: boolean }>(endpoint, { cache: "no-store" });
      setFavorited(response.is_favorited);
    } catch { /* Show neutral state until user interacts. */ }
  };
  const toggleFavorite = async () => {
    if (busy) return;
    setBusy(true); setNotice("");
    try {
      await ensureFavoriteState();
      const response = await apiRequest<{ is_favorited: boolean }>(endpoint, { method: favorited ? "DELETE" : "POST" });
      setFavorited(response.is_favorited); setNotice(response.is_favorited ? (english ? "Added to favorites" : "به علاقه‌مندی‌ها افزوده شد") : (english ? "Removed from favorites" : "از علاقه‌مندی‌ها حذف شد"));
    } catch (error) {
      setNotice(error instanceof ApiError && error.status === 401 ? (english ? "Sign in to favorite" : "برای پسندیدن وارد حساب شوید") : (english ? "Could not save favorite" : "ثبت پسند ناموفق بود"));
    } finally { setBusy(false); }
  };
  const compare = () => {
    const key = "productCompareSlugs";
    let current: string[] = [];
    try {
      const stored = JSON.parse(window.localStorage.getItem(key) || "[]");
      if (Array.isArray(stored)) current = stored.filter((slug): slug is string => typeof slug === "string");
    } catch { current = []; }
    const next = current.includes(product.slug) ? current.filter((slug) => slug !== product.slug) : [...current.slice(-3), product.slug];
    window.localStorage.setItem(key, JSON.stringify(next));
    window.dispatchEvent(new CustomEvent("product-compare-updated", { detail: next }));
    setNotice(next.includes(product.slug) ? (english ? "Added for comparison" : "برای مقایسه اضافه شد") : (english ? "Removed from comparison" : "از مقایسه حذف شد"));
  };
  const share = async () => {
    const url = `${window.location.origin}/${locale}/product/${product.slug}`;
    try {
      if (navigator.share) await navigator.share({ title: product.name, url });
      else { await navigator.clipboard.writeText(url); setNotice(english ? "Product link copied" : "پیوند محصول کپی شد"); }
    } catch { /* The share sheet was dismissed; no error message is needed. */ }
  };
  return <div className="product-card-social-actions" aria-label={english ? "Product tools" : "ابزارهای محصول"}><button type="button" onClick={compare} title={english ? "Compare" : "مقایسه"} aria-label={`${english ? "Compare" : "مقایسه"} ${product.name}`}>⇄</button><button type="button" onClick={toggleFavorite} disabled={busy} title={english ? "Favorite" : "پسندیدن"} aria-label={`${favorited ? (english ? "Remove from favorites" : "حذف از علاقه‌مندی") : (english ? "Add to favorites" : "افزودن به علاقه‌مندی")} ${product.name}`} className={favorited ? "is-active" : ""}>♥</button><button type="button" onClick={share} title={english ? "Share" : "اشتراک‌گذاری"} aria-label={`${english ? "Share" : "اشتراک‌گذاری"} ${product.name}`}>↗</button>{notice && <span role="status">{notice}</span>}</div>;
}

export function ProductCardSkeleton() {
  return (
    <div className="industrial-product-card catalog-loading-card animate-pulse" aria-hidden="true">
      <div className="industrial-card-image industrial-card-image--skeleton">
        <Skeleton className="h-full w-full" />
      </div>
      <div className="industrial-card-content">
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-1/3 rounded" />
          <Skeleton className="h-3 w-1/4 rounded" />
        </div>
        <Skeleton className="mt-3 h-4 w-4/5 rounded" />
        <Skeleton className="mt-1.5 h-4 w-3/5 rounded" />
        <Skeleton className="mt-3 h-3 w-2/5 rounded" />
        <div className="mt-3 flex items-center justify-between border-t pt-2 border-border/40">
          <Skeleton className="h-3 w-1/4 rounded" />
          <Skeleton className="h-3 w-1/5 rounded" />
        </div>
        <div className="mt-auto pt-3 flex flex-col items-end">
          <Skeleton className="h-5 w-2/5 rounded" />
        </div>
      </div>
      <div className="industrial-card-actions">
        <Skeleton className="h-[38px] w-full rounded-lg" />
      </div>
    </div>
  );
}
