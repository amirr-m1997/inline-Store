"use client";

import { useEffect, useRef, useState } from "react";

const sortOptions = [
  { value: "code", fa: "کد کالا", en: "Product code" },
  { value: "name", fa: "نام کالا", en: "Product name" },
  { value: "-created_at", fa: "جدیدترین", en: "Newest" },
];

export function CatalogSortSelect({ value, onChange, label, id, locale = "fa" }: { value: string; onChange: (value: string) => void; label: string; id?: string; locale?: string }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onDown = (event: Event) => { if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false); };
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("touchstart", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);
  const english = locale === "en";
  const current = sortOptions.find((option) => option.value === value) ?? sortOptions[0];
  return <div ref={rootRef} className="catalog-sort-select">
    <button type="button" id={id} className="catalog-sort-select-trigger" aria-label={label} aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((value) => !value)}><span>{english ? current.en : current.fa}</span><i aria-hidden="true">▾</i></button>
    {open && <div className="catalog-sort-select-menu" role="listbox" aria-label={label}>{sortOptions.map((option) => <button key={option.value} type="button" role="option" aria-selected={option.value === value} className={option.value === value ? "is-active" : undefined} onClick={() => { onChange(option.value); setOpen(false); }}>{english ? option.en : option.fa}</button>)}</div>}
  </div>;
}