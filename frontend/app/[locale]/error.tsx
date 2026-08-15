"use client";
export default function CatalogError({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <main className="catalog-experience site-container"><div className="empty-state catalog-api-error"><p>دریافت کاتالوگ ناموفق بود.</p><button type="button" onClick={reset}>تلاش دوباره</button></div></main>; }
