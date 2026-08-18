import { ProductCard, ProductCardSkeleton } from "./product-card";
import type { ProductPage } from "../../lib/api/products";

export function ProductGrid({ products, loading, locale }: { products: ProductPage | null; loading: boolean; locale: string }) {
  const hasProducts = Boolean(products?.results.length);

  // Keep current cards mounted while a new query is in flight. Replacing
  // them with skeletons made every client navigation look like a full refresh.
  if (loading && !hasProducts) {
    return <div className="industrial-product-grid catalog-card-grid" aria-busy="true" aria-label="در حال دریافت محصولات">{Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}</div>;
  }

  return <div className={`catalog-products-view${loading ? " is-loading" : ""}`} aria-busy={loading}>
    <div className="industrial-product-grid catalog-card-grid">
      {products?.results.map((product) => <ProductCard key={product.id} product={product} locale={locale} />)}
    </div>
    {loading && <div className="catalog-products-loading" role="status" aria-live="polite"><span aria-hidden="true" />در حال به‌روزرسانی محصولات…</div>}
  </div>;
}
