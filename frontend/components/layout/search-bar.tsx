"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

export function SearchBar() {
  const router = useRouter();
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [query, setQuery] = useState("");
  const clear = () => setQuery("");
  return <form className="reference-search" role="search" onSubmit={(event) => { event.preventDefault(); const value = query.trim(); router.push(`/${locale}/search${value ? `?q=${encodeURIComponent(value)}` : ""}`); }}><label className="sr-only" htmlFor="site-search">جست‌وجوی محصولات، برندها و دانش</label><input className="reference-search-input" id="site-search" dir={locale === "en" ? "ltr" : "rtl"} value={query} onChange={(event) => setQuery(event.target.value)} aria-label="جست‌وجوی محصولات، کد فنی، برند و دانش صنعتی" placeholder="جستجو در محصولات، برندها و دانش صنعتی..." />{query && <button className="reference-search-clear" type="button" onClick={clear} aria-label="پاک کردن جست‌وجو">×</button>}<button className="reference-search-submit" type="submit" aria-label="جست‌وجو">⌕</button></form>;
}
