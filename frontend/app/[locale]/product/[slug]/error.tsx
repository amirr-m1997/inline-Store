"use client";

export default function ProductError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="product-detail-page site-container"><div className="product-state product-error"><p>دریافت اطلاعات محصول ناموفق بود.</p><button type="button" onClick={reset}>تلاش دوباره</button></div></main>;
}
