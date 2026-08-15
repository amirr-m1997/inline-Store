export type ActiveCatalogFilter = { key: string; label: string; onRemove: () => void };

export function ActiveFilterSummary({ filters, onClearAll }: { filters: ActiveCatalogFilter[]; onClearAll: () => void }) {
  if (!filters.length) return null;
  return <div className="catalog-active-filters" aria-label="فیلترهای فعال">{filters.map((filter) => <button type="button" key={filter.key} onClick={filter.onRemove}>{filter.label} ×</button>)}<button type="button" className="catalog-clear-all" onClick={onClearAll}>حذف همه</button></div>;
}
