"use client";

import { CatalogSortSelect } from "./catalog-sort-select";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { formatNumber } from "../../lib/product/formatters";

function ShopCatalogTabs() {
  const pathname = usePathname(), router = useRouter(), params = useSearchParams();
  if (!/\/shop\/?$/.test(pathname)) return null;
  const active = params.get("catalog") || "all";
  const choose = (tab: string) => {
    const next = new URLSearchParams(params.toString());
    const settings: Record<string, Record<string, string | null>> = {
      all: { catalog: null, featured: null, discounted: null, condition: null, ordering: null },
      featured: { catalog: "featured", featured: "1", discounted: null, condition: null, ordering: null },
      newest: { catalog: "newest", featured: null, discounted: null, condition: null, ordering: "-created_at" },
      discounted: { catalog: "discounted", featured: null, discounted: "1", condition: null, ordering: "-discount_percentage" },
      used: { catalog: "used", featured: null, discounted: null, condition: "used", ordering: null },
    };
    Object.entries(settings[tab]).forEach(([key, value]) => value ? next.set(key, value) : next.delete(key)); next.delete("page"); next.delete("cursor"); router.push(`${pathname}?${next}`);
  };
  return <nav className="shop-catalog-tabs" aria-label="نمایش محصولات">{[["all", "همه محصولات"], ["featured", "محصولات ویژه"], ["newest", "جدیدترین‌ها"], ["discounted", "تخفیف‌دار"], ["used", "کارکرده"]].map(([value, label]) => <button key={value} type="button" onClick={() => choose(value)} className={active === value ? "is-active" : undefined}>{label}</button>)}</nav>;
}

export function CatalogToolbar({ query, ordering, inStock, hasImage = false, resultCount, searchLoading, activeFilterCount = 0, onSearch, onOrderingChange, onStockChange, onImageChange, onOpenFilters }: { query?: string; ordering: string; inStock: boolean; hasImage?: boolean; resultCount: number; searchLoading: boolean; activeFilterCount?: number; onSearch: (value: string) => void; onOrderingChange: (value: string) => void; onStockChange: (value: boolean) => void; onImageChange?: (value: boolean) => void; onOpenFilters: () => void }) {
  void query; void resultCount; void searchLoading; void onSearch;
  return <div className="catalog-toolbar" aria-label="کنترل‌های کاتالوگ"><ShopCatalogTabs /><div className="catalog-filters"><div className="catalog-sort-control"><label htmlFor="catalog-sort-ordering">مرتب‌سازی</label><CatalogSortSelect id="catalog-sort-ordering" value={ordering} onChange={onOrderingChange} label="مرتب‌سازی" /></div><label className="stock-filter"><input type="checkbox" checked={inStock} onChange={(event) => onStockChange(event.target.checked)} /> <span>فقط موجود</span></label><label className="stock-filter"><input type="checkbox" checked={hasImage} onChange={(event) => onImageChange?.(event.target.checked)} /> <span>فقط محصولات عکس‌دار</span></label><button className="spec-filter" type="button" onClick={onOpenFilters} aria-label={`باز کردن فیلترها${activeFilterCount ? `، ${activeFilterCount.toLocaleString("fa-IR")} فیلتر فعال` : ""}`}><span>فیلترها</span>{activeFilterCount > 0 && <b aria-hidden="true">{activeFilterCount.toLocaleString("fa-IR")}</b>}</button></div></div>;
}
