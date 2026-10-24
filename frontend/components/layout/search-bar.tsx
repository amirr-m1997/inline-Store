"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { getProducts } from "../../lib/api/products";
import type { CatalogProduct } from "../catalog/product-card";

const MIN_QUERY_LENGTH = 3;
const DEBOUNCE_MS = 400;
const MAX_SUGGESTIONS = 8;

export function SearchBar() {
  const router = useRouter();
  const { locale = "fa" } = useParams<{ locale: string }>();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<CatalogProduct[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const formRef = useRef<HTMLFormElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const term = query.trim();
  const english = locale === "en";
  const productHref = (item: CatalogProduct) => `/${locale}/product/${item.slug}`;

  useEffect(() => {
    controllerRef.current?.abort();
    if (term.length < MIN_QUERY_LENGTH) {
      setSuggestions([]);
      setLoading(false);
      setOpen(false);
      setActiveIndex(-1);
      return;
    }
    setLoading(true);
    const timer = window.setTimeout(() => {
      const controller = new AbortController();
      controllerRef.current = controller;
      getProducts({ search: term, page_size: MAX_SUGGESTIONS }, controller.signal)
        .then((page) => {
          if (controller.signal.aborted) return;
          setSuggestions((page.results ?? []).slice(0, MAX_SUGGESTIONS));
          setLoading(false);
          setOpen(true);
          setActiveIndex(-1);
        })
        .catch(() => {
          if (controller.signal.aborted) return;
          setSuggestions([]);
          setLoading(false);
        });
    }, DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [term]);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!formRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") { setOpen(false); return; }
    if (!suggestions.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((current) => (current + 1) % suggestions.length);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => (current <= 0 ? suggestions.length - 1 : current - 1));
      return;
    }
    if (event.key === "Enter" && open && activeIndex >= 0) {
      const item = suggestions[activeIndex];
      if (!item) return;
      event.preventDefault();
      setOpen(false);
      router.push(productHref(item));
    }
  };

  const showPanel = open && (loading || suggestions.length > 0 || term.length >= MIN_QUERY_LENGTH);

  const clear = () => { setQuery(""); setOpen(false); setSuggestions([]); setActiveIndex(-1); };

  return <form
    ref={formRef}
    className={`reference-search${showPanel ? " has-suggestions" : ""}`}
    role="search"
    onSubmit={(event) => { event.preventDefault(); const value = query.trim(); setOpen(false); router.push(`/${locale}/search${value ? `?q=${encodeURIComponent(value)}` : ""}`); }}
  >
    <label className="sr-only" htmlFor="site-search">جست‌وجوی محصولات، برندها و دانش</label>
    <input
      className="reference-search-input"
      id="site-search"
      dir={english ? "ltr" : "rtl"}
      value={query}
      onChange={(event) => setQuery(event.target.value)}
      onKeyDown={onInputKeyDown}
      onFocus={() => { if (term.length >= MIN_QUERY_LENGTH && suggestions.length) setOpen(true); }}
      aria-label="جست‌وجوی محصولات، کد فنی، برند و دانش صنعتی"
      placeholder="جستجو در محصولات، برندها و دانش صنعتی..."
      role="combobox"
      aria-expanded={showPanel}
      aria-controls="site-search-suggestions"
      aria-autocomplete="list"
      aria-activedescendant={activeIndex >= 0 && suggestions[activeIndex] ? `site-search-option-${suggestions[activeIndex].id}` : undefined}
      autoComplete="off"
    />
    {query && <button className="reference-search-clear" type="button" onClick={clear} aria-label="پاک کردن جست‌وجو">×</button>}
    <button className="reference-search-submit" type="submit" aria-label="جست‌وجو">⌕</button>
    {showPanel && <div className="reference-search-suggestions" id="site-search-suggestions" role="listbox" aria-label="پیشنهادهای جست‌وجو">
      {loading && !suggestions.length && <p className="reference-search-state" role="status">{english ? "Searching…" : "در حال جست‌وجو…"}</p>}
      {!loading && !suggestions.length && <p className="reference-search-state" role="status">{english ? "No matching products." : "محصولی مطابق عبارت جست‌وجو پیدا نشد."}</p>}
      {suggestions.map((item, index) => {
        const thumb = item.images?.find((image) => image.is_primary)?.image ?? item.images?.[0]?.image;
        return <Link
          key={item.id}
          className="reference-suggestion"
          id={`site-search-option-${item.id}`}
          role="option"
          aria-selected={index === activeIndex}
          href={productHref(item)}
          onMouseEnter={() => setActiveIndex(index)}
          onClick={() => setOpen(false)}
        >
          <span className="reference-suggestion-thumb">{thumb ? <Image src={thumb} alt="" aria-hidden="true" fill sizes="44px" /> : <i aria-hidden="true">◇</i>}</span>
          <span className="reference-suggestion-body">
            <b>{item.name}</b>
            <small><bdi dir="ltr">{item.code}</bdi>{item.category ? ` · ${item.category.name_fa}` : ""}</small>
          </span>
        </Link>;
      })}
      {suggestions.length > 0 && <Link className="reference-search-all" href={`/${locale}/search?q=${encodeURIComponent(term)}`} onClick={() => setOpen(false)}>{english ? "See all results" : "مشاهده همه نتایج"}</Link>}
    </div>}
  </form>;
}
