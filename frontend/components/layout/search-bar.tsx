"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { getCategorySearchUrl } from "../../lib/category-url";

export function SearchBar() {
  const router = useRouter();
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [query, setQuery] = useState("");
  return <form className="reference-search" onSubmit={(event) => { event.preventDefault(); router.push(getCategorySearchUrl(locale, query)); }}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="جستجو بر اساس نام کالا، کد فنی، SKU یا برند..." /><button aria-label="جست‌وجو">⌕</button></form>;
}
