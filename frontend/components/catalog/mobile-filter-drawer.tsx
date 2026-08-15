"use client";

import { useEffect, useState } from "react";
import type { CatalogFacet } from "./facet-types";
import { FacetSidebar } from "./facet-sidebar";
import { Drawer } from "../ui/drawer";

export function MobileFilterDrawer({ open, ordering, inStock, resultCount = 0, activeFilterCount = 0, facets = [], onClose, onApply, onReset, onFacetOptionChange, onFacetRangeChange }: { open: boolean; ordering: string; inStock: boolean; resultCount?: number; activeFilterCount?: number; facets?: CatalogFacet[]; onClose: () => void; onApply: (ordering: string, inStock: boolean) => void; onReset?: () => void; onFacetOptionChange?: (facet: CatalogFacet, value: string, selected: boolean) => void; onFacetRangeChange?: (facet: CatalogFacet, value: { min?: string; max?: string }) => void }) {
  const [nextOrdering, setNextOrdering] = useState(ordering);
  const [nextInStock, setNextInStock] = useState(inStock);
  useEffect(() => { setNextOrdering(ordering); setNextInStock(inStock); }, [ordering, inStock, open]);
  if (!open) return null;
  return <Drawer open={open} onClose={onClose} title={`فیلترهای کاتالوگ${activeFilterCount ? ` (${activeFilterCount.toLocaleString("fa-IR")} فعال)` : ""}`} className="catalog-filter-drawer" overlayClassName="catalog-drawer-backdrop"><div className="catalog-filter-drawer-content"><p className="catalog-filter-result-count" role="status" aria-live="polite">{resultCount.toLocaleString("fa-IR")} محصول با این فیلترها</p><div><label htmlFor="catalog-drawer-sort-ordering">مرتب‌سازی</label><select id="catalog-drawer-sort-ordering" value={nextOrdering} onChange={(event) => setNextOrdering(event.target.value)}><option value="code">کد کالا</option><option value="name">نام کالا</option><option value="-created_at">جدیدترین</option></select></div><label className="drawer-checkbox"><input type="checkbox" checked={nextInStock} onChange={(event) => setNextInStock(event.target.checked)} /><span>فقط موجود</span></label>{facets.length > 0 && <FacetSidebar facets={facets} onOptionChange={(facet, value, selected) => onFacetOptionChange?.(facet, value, selected)} onRangeChange={(facet, value) => onFacetRangeChange?.(facet, value)} />}</div><footer><button type="button" className="catalog-filter-reset" onClick={() => { setNextOrdering("code"); setNextInStock(false); onReset?.(); }}>پاک‌سازی فیلترها</button><button type="button" className="catalog-filter-apply" onClick={() => { onApply(nextOrdering, nextInStock); onClose(); }}>نمایش نتایج ({resultCount.toLocaleString("fa-IR")})</button></footer></Drawer>;
}
