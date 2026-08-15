export function ActiveFilterChips({ query, inStock, onClearQuery, onClearStock, onClearAll }: { query?: string; inStock: boolean; onClearQuery: () => void; onClearStock: () => void; onClearAll: () => void }) {
  if (!query && !inStock) return null;
  return <div className="catalog-active-filters" aria-label="فیلترهای فعال">{query && <button type="button" onClick={onClearQuery}>جست‌وجو: {query} ×</button>}{inStock && <button type="button" onClick={onClearStock}>فقط موجود ×</button>}<button type="button" className="catalog-clear-all" onClick={onClearAll}>حذف همه</button></div>;
}
