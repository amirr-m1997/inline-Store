"use client";

import { useEffect, useRef, useState } from "react";

export function SearchBox({ value = "", loading = false, onSearch, onSuggest }: { value?: string; loading?: boolean; onSearch: (value: string) => void; onSuggest?: (value: string) => void }) {
  const [draft, setDraft] = useState(value);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => setDraft(value), [value]);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  const submit = (next = draft) => { if (timer.current) clearTimeout(timer.current); onSearch(next.trim()); };
  const change = (next: string) => { setDraft(next); onSuggest?.(next); if (timer.current) clearTimeout(timer.current); timer.current = setTimeout(() => onSearch(next.trim()), 450); };
  return <label className="catalog-search-box"><span>جست‌وجوی فنی</span><div className="catalog-search-control"><input value={draft} placeholder="نام، SKU، شماره فنی یا کد کالا" aria-label="جست‌وجوی نام، SKU یا کد فنی" aria-busy={loading} onChange={(event) => change(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") submit(); if (event.key === "Escape") { setDraft(""); submit(""); } }} />{draft && <button type="button" onClick={() => { setDraft(""); submit(""); }} aria-label="پاک کردن جست‌وجو">×</button>}{loading && <span className="catalog-search-loading" role="status" aria-label="در حال جست‌وجو">…</span>}</div></label>;
}
