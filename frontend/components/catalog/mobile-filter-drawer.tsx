"use client";

import { useEffect, useState } from "react";
import type { CatalogFacet } from "./facet-types";
import { FacetSidebar } from "./facet-sidebar";
import { CatalogSortSelect } from "./catalog-sort-select";
import { Drawer } from "../ui/drawer";

export function MobileFilterDrawer({ open, ordering, inStock, hasImage = false, resultCount = 0, activeFilterCount = 0, facets = [], onClose, onApply, onReset, onFacetOptionChange, onFacetRangeChange }: { open: boolean; ordering: string; inStock: boolean; hasImage?: boolean; resultCount?: number; activeFilterCount?: number; facets?: CatalogFacet[]; onClose: () => void; onApply: (ordering: string, inStock: boolean, hasImage: boolean) => void; onReset?: () => void; onFacetOptionChange?: (facet: CatalogFacet, value: string, selected: boolean) => void; onFacetRangeChange?: (facet: CatalogFacet, value: { min?: string; max?: string }) => void }) {
  const [nextOrdering, setNextOrdering] = useState(ordering);
  const [nextInStock, setNextInStock] = useState(inStock), [nextHasImage, setNextHasImage] = useState(hasImage);
  useEffect(() => { setNextOrdering(ordering); setNextInStock(inStock); setNextHasImage(hasImage); }, [ordering, inStock, hasImage, open]);
  if (!open) return null;
  return <Drawer open={open} onClose={onClose} title={`فیلترهای کاتالوگ${activeFilterCount ? ` (${activeFilterCount.toLocaleString("fa-IR")} فعال)` : ""}`} className="catalog-filter-drawer" overlayClassName="catalog-drawer-backdrop"><div className="catalog-filter-drawer-content"><p className="catalog-filter-result-count" role="status" aria-live="polite">{resultCount.toLocaleString("fa-IR")} محصول با این فیلترها</p><div><label htmlFor="catalog-drawer-sort-ordering">مرتب‌سازی</label><CatalogSortSelect id="catalog-drawer-sort-ordering" value={nextOrdering} onChange={setNextOrdering} label="مرتب‌سازی" /></div><label className="drawer-checkbox"><input type="checkbox" checked={nextInStock} onChange={(event) => setNextInStock(event.target.checked)} /><span>فقط موجود</span></label><label className="drawer-checkbox"><input type="checkbox" checked={nextHasImage} onChange={(event) => setNextHasImage(event.target.checked)} /><span>فقط محصولات عکس‌دار</span></label>{facets.length > 0 && <FacetSidebar facets={facets} onOptionChange={(facet, value, selected) => onFacetOptionChange?.(facet, value, selected)} onRangeChange={(facet, value) => onFacetRangeChange?.(facet, value)} />}</div><footer><button type="button" className="catalog-filter-reset" onClick={() => { setNextOrdering("code"); setNextInStock(false); setNextHasImage(false); onReset?.(); }}>پاک‌سازی فیلترها</button><button type="button" className="catalog-filter-apply" onClick={() => { onApply(nextOrdering, nextInStock, nextHasImage); onClose(); }}>نمایش نتایج ({resultCount.toLocaleString("fa-IR")})</button></footer></Drawer>;
}
