import { ProductCard as DomainProductCard } from "../product/product-card/product-card";
import { Skeleton } from "../ui/skeleton";
import { toProductSummary } from "../../lib/product/adapters";

export type CatalogProduct = {
  id: number;
  name: string;
  slug: string;
  code: string;
  unit: string;
  available_quantity: number | null;
  category: { name_fa: string } | null;
  images: { image: string; alt_text: string; alt_fa?: string; is_primary?: boolean }[];
  price: { original_amount: string; final_amount: string; discount_percentage: string } | null;
};

const money = (value: string) => Number(value).toLocaleString("fa-IR", { maximumFractionDigits: 0 });

export function ProductCard({ product, priority = false, locale = "fa" }: { product: CatalogProduct; priority?: boolean; locale?: string }) {
  return <DomainProductCard product={toProductSummary(product)} priority={priority} locale={locale} />;
}

export function ProductCardSkeleton() {
  return <div className="industrial-product-card catalog-loading-card animate-pulse p-4 rounded-xl border shadow-sm">
    <Skeleton className="h-48 w-full rounded-lg" />
    <Skeleton className="mt-4 h-3 w-1/4 rounded" />
    <Skeleton className="mt-2 h-5 w-4/5 rounded" />
    <Skeleton className="mt-2 h-3 w-1/3 rounded" />
    <div className="mt-4 flex items-center justify-between">
      <Skeleton className="h-4 w-1/3 rounded" />
      <Skeleton className="h-4 w-1/4 rounded" />
    </div>
    <Skeleton className="mt-4 h-10 w-full rounded-lg" />
  </div>;
}
