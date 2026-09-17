import { Skeleton } from "../ui/skeleton";

export function ProductDetailSkeleton() {
  return (
    <main className="product-detail-page site-container" aria-busy="true" aria-label="در حال بارگذاری اطلاعات محصول">
      {/* Breadcrumb Skeleton */}
      <div className="product-breadcrumb flex items-center gap-2 py-3" aria-hidden="true">
        <Skeleton className="h-4 w-12 rounded" />
        <span className="text-border">/</span>
        <Skeleton className="h-4 w-20 rounded" />
        <span className="text-border">/</span>
        <Skeleton className="h-4 w-32 rounded" />
      </div>

      {/* Main Purchase Layout */}
      <section className="product-purchase-layout" aria-hidden="true">
        {/* Buy Panel */}
        <aside className="product-buy-panel">
          <Skeleton className="h-4 w-28 rounded" />
          <Skeleton className="mt-3 h-8 w-4/5 rounded" />
          <Skeleton className="mt-2 h-4 w-1/3 rounded" />

          <div className="mt-4 flex items-center gap-3">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-4 w-24 rounded" />
          </div>

          <div className="mt-6 rounded-xl border border-border/50 p-4 bg-surface-secondary/40">
            <Skeleton className="h-4 w-16 rounded" />
            <Skeleton className="mt-2 h-8 w-36 rounded" />
          </div>

          <div className="mt-6 flex items-center gap-4">
            <Skeleton className="h-11 w-32 rounded-lg" />
            <Skeleton className="h-11 flex-1 rounded-lg" />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 border-t border-border/40 pt-4">
            <Skeleton className="h-12 rounded-lg" />
            <Skeleton className="h-12 rounded-lg" />
          </div>
        </aside>

        {/* Gallery */}
        <div className="product-gallery">
          <div className="product-gallery-stage aspect-square w-full rounded-2xl border border-border/60 overflow-hidden bg-surface-secondary/30 flex items-center justify-center p-6">
            <Skeleton className="h-4/5 w-4/5 rounded-xl" />
          </div>
          <div className="mt-4 flex items-center gap-3 justify-center">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-16 rounded-xl border border-border/50" />
            ))}
          </div>
        </div>
      </section>

      {/* Tabs Skeleton */}
      <section className="mt-10 rounded-2xl border border-border/60 p-6 bg-surface" aria-hidden="true">
        <div className="flex items-center gap-6 border-b border-border pb-4">
          <Skeleton className="h-6 w-28 rounded" />
          <Skeleton className="h-6 w-28 rounded" />
          <Skeleton className="h-6 w-28 rounded" />
        </div>
        <div className="mt-6 space-y-3">
          <Skeleton className="h-4 w-full rounded" />
          <Skeleton className="h-4 w-11/12 rounded" />
          <Skeleton className="h-4 w-4/5 rounded" />
          <Skeleton className="h-4 w-2/3 rounded" />
        </div>
      </section>
    </main>
  );
}
