import { ProductCardSkeleton } from "../catalog/product-card";
import { Skeleton } from "../ui/skeleton";

export function SearchSkeleton() {
  return (
    <main className="site-search-page site-container py-8" aria-busy="true" aria-label="در حال جست‌وجو...">
      {/* Search Header / Entry Form Skeleton */}
      <div className="mx-auto max-w-2xl text-center space-y-4 mb-10">
        <Skeleton className="mx-auto h-8 w-48 rounded" />
        <Skeleton className="mx-auto h-12 w-full max-w-xl rounded-xl border border-border/50" />
      </div>

      {/* Group Summary Pills Skeleton */}
      <div className="flex items-center justify-center gap-3 mb-8" aria-hidden="true">
        <Skeleton className="h-8 w-24 rounded-full" />
        <Skeleton className="h-8 w-28 rounded-full" />
        <Skeleton className="h-8 w-20 rounded-full" />
        <Skeleton className="h-8 w-32 rounded-full" />
      </div>

      {/* Products Group Skeleton */}
      <section className="site-search-group mb-12" aria-hidden="true">
        <div className="flex items-center justify-between mb-6 pb-2 border-b border-border">
          <Skeleton className="h-6 w-32 rounded" />
          <Skeleton className="h-4 w-20 rounded" />
        </div>
        <div className="industrial-product-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      </section>

      {/* Categories & Brands Skeleton */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8" aria-hidden="true">
        <div className="p-6 rounded-2xl border border-border bg-surface">
          <Skeleton className="h-6 w-32 rounded mb-4" />
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 rounded-lg" />
            ))}
          </div>
        </div>
        <div className="p-6 rounded-2xl border border-border bg-surface">
          <Skeleton className="h-6 w-32 rounded mb-4" />
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 rounded-lg" />
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
