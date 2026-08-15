import { ProductCard, ProductCardSkeleton } from "./product-card";
import type { ProductPage } from "../../lib/api/products";

export function ProductGrid({ products, loading, locale }: { products: ProductPage | null; loading: boolean; locale: string }) {
  if (loading) return <div className="industrial-product-grid catalog-card-grid">{Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}</div>;
  return <div className="industrial-product-grid catalog-card-grid">{products?.results.map((product) => <ProductCard key={product.id} product={product} locale={locale} />)}</div>;
}
