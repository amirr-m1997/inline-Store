"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";
import { getCategories } from "../../lib/api/products";
import { getNavigation } from "../../lib/api/content";
import { formatNumber } from "../../lib/product/formatters";

type NavigationItem = { id: number; title_fa: string; url: string; icon: string };
export type CategoryTreeNode = { id: number; code: string; name_fa: string; name_en: string; slug: string; level: number; product_count: number; children: CategoryTreeNode[] };
type CategoryNavigationProps = { mobileOpen: boolean; onNavigate: () => void };

function asArray<T>(data: unknown): T[] { return Array.isArray(data) ? data as T[] : []; }

export function CategoryNavigation({ mobileOpen, onNavigate }: CategoryNavigationProps) {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const navigationRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [items, setItems] = useState<NavigationItem[]>([]);
  const [roots, setRoots] = useState<CategoryTreeNode[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeRootId, setActiveRootId] = useState<number | null>(null);
  const [mobileMode, setMobileMode] = useState<"main" | "categories">("main");
  const [mobilePath, setMobilePath] = useState<CategoryTreeNode[]>([]);

  useEffect(() => {
    getNavigation<NavigationItem[]>().then((data) => setItems(asArray<NavigationItem>(data))).catch(() => setItems([]));
  }, []);
  const loadTree = () => {
    if (roots.length || loading) return;
    setLoading(true);
    getCategories()
      .then((data) => { const tree = asArray<CategoryTreeNode>(data); setRoots(tree); setActiveRootId(tree[0]?.id ?? null); })
      .catch(() => setRoots([])).finally(() => setLoading(false));
  };
  const toggleCategories = () => { setMobilePath([]); setMobileMode("categories"); setOpen((current) => { const next = !current; if (next) loadTree(); return next; }); };
  const closeCategories = () => { setOpen(false); setMobileMode("main"); setMobilePath([]); };
  const returnToMainMenu = () => { setMobileMode("main"); setMobilePath([]); };
  const closeAll = () => { closeCategories(); onNavigate(); };
  const mobileLevel = mobilePath.length ? mobilePath[mobilePath.length - 1].children : roots;
  const mobileTitle = mobilePath.length ? mobilePath[mobilePath.length - 1].name_fa : null;
  const mobileGoBack = () => { if (mobilePath.length) setMobilePath((path) => path.slice(0, -1)); else returnToMainMenu(); };
  const mobileDrill = (node: CategoryTreeNode, event: { preventDefault(): void }) => { if (node.children?.length) { event.preventDefault(); setMobilePath((path) => [...path, node]); } else closeAll(); };

  useEffect(() => {
    if (!mobileOpen) closeCategories();
  }, [mobileOpen]);
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const onPointerDown = (event: PointerEvent) => { if (!navigationRef.current?.contains(event.target as Node)) closeCategories(); };
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") { closeCategories(); triggerRef.current?.focus(); return; } if (event.key !== "Tab" || !mobileOpen) return; const focusable = navigationRef.current?.querySelectorAll<HTMLElement>('a,button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])'); if (!focusable?.length) return; const first = focusable[0]; const last = focusable[focusable.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => { document.removeEventListener("pointerdown", onPointerDown); document.removeEventListener("keydown", onKeyDown); previous?.focus(); };
  }, [mobileOpen, open]);

  const localizeUrl = useCallback((url: string) => url.replace(/^\/(?:fa|en)(?=\/|$)/, `/${locale}`).replace(/\/$/, "") || `/${locale}`, [locale]);
  const navCurrent = useCallback((url: string) => {
    const target = localizeUrl(url);
    return pathname === target || (target !== `/${locale}` && pathname.startsWith(`${target}/`)) ? "page" as const : undefined;
  }, [locale, localizeUrl, pathname]);
  const ordinaryItems = useMemo(() => items.filter((item) => {
    const normalizedUrl = localizeUrl(item.url);
    return !normalizedUrl.includes("/categor")
      && !item.title_fa.includes("دسته‌بندی")
      && normalizedUrl !== `/${locale}/shop`
      && normalizedUrl !== `/${locale}/support`
      && !normalizedUrl.startsWith(`/${locale}/support/`)
      && item.title_fa !== "فروشگاه";
  }), [items, locale, localizeUrl]);
  const homeItems = ordinaryItems.filter((item) => localizeUrl(item.url) === `/${locale}` || item.title_fa === "صفحه اصلی");
  const remainingItems = ordinaryItems.filter((item) => !homeItems.includes(item));
  const supportActive = pathname === `/${locale}/support` || pathname.startsWith(`/${locale}/support/`);
  const activeRoot = roots.find((root) => root.id === activeRootId) ?? roots[0];
  return <nav id="site-mobile-navigation" ref={navigationRef} className={`reference-category-nav responsive-container${mobileOpen ? " mobile-open" : ""}${mobileMode === "categories" ? " category-mode" : ""}`} aria-label="ناوبری وب‌سایت">
    <div className="reference-nav-links">
      {(!mobileOpen || mobileMode === "main") && <><div className="category-nav-section"><span className="mobile-nav-section-label">دسته‌بندی محصولات</span><button ref={triggerRef} className="category-menu-trigger" type="button" onClick={toggleCategories} aria-expanded={open} aria-controls="product-category-menu"><span className="category-menu-icon" aria-hidden="true"><i /><i /><i /></span><b>دسته‌بندی محصولات</b><i aria-hidden="true">⌄</i></button></div>
      <div className="reference-primary-links">{homeItems.map((item) => <Link key={item.id} href={localizeUrl(item.url)} onClick={closeAll} aria-current={navCurrent(item.url)}>{item.icon && <span aria-hidden="true">{item.icon}</span>}{locale === "en" ? "Home" : "صفحه اصلی"}</Link>)}<Link href={`/${locale}/shop`} onClick={closeAll} aria-current={navCurrent(`/${locale}/shop`)}>{locale === "en" ? "All products" : "همه محصولات"}</Link><Link href={`/${locale}/newest`} onClick={closeAll} aria-current={navCurrent(`/${locale}/newest`)}>{locale === "en" ? "Latest" : "جدیدترین‌ها"}</Link><Link href={`/${locale}/best-discounts`} onClick={closeAll} aria-current={navCurrent(`/${locale}/best-discounts`)}>{locale === "en" ? "Best discounts" : "بیشترین تخفیف"}</Link><Link href={`/${locale}/knowledge`} onClick={closeAll} aria-current={navCurrent(`/${locale}/knowledge`)}>{locale === "en" ? "Knowledge & News" : "دانش و اخبار"}</Link><Link href={`/${locale}/rfq`} onClick={closeAll} aria-current={navCurrent(`/${locale}/rfq`)}>{locale === "en" ? "Request a Quote" : "استعلام قیمت"}</Link><Link href={`/${locale}/support`} onClick={closeAll} aria-current={supportActive ? "page" : undefined}>{locale === "en" ? "Customer Service" : "امور مشتریان"}</Link>{remainingItems.map((item) => <Link key={item.id} href={localizeUrl(item.url)} onClick={closeAll} aria-current={navCurrent(item.url)}>{item.icon && <span aria-hidden="true">{item.icon}</span>}{item.title_fa}</Link>)}</div></>}
    </div>

    {open && <section id="product-category-menu" className="product-category-menu" aria-label="دسته‌بندی محصولات">
      <div className="desktop-category-menu">
        <aside aria-label="دسته‌بندی‌های اصلی">
          <header><b>گروه‌های اصلی</b><small>{formatNumber(roots.length)} گروه</small></header>
          {loading && <p className="category-menu-state">در حال دریافت دسته‌بندی‌ها…</p>}
          {!loading && !roots.length && <p className="category-menu-state">دسته‌بندی‌ای یافت نشد.</p>}
          {roots.map((root) => <div className={`root-category-row${root.id === activeRoot?.id ? " active" : ""}`} key={root.id} onMouseEnter={() => setActiveRootId(root.id)}>
            <button type="button" onFocus={() => setActiveRootId(root.id)} onClick={() => setActiveRootId(root.id)} aria-pressed={root.id === activeRoot?.id}><span>{root.name_fa}</span><small>{formatNumber(root.product_count)}</small></button>
            <Link href={getCategoryUrl(root, locale)} onClick={closeAll} aria-label={`مشاهده ${root.name_fa}`}><span className="category-direction-indicator" aria-hidden="true" /></Link>
          </div>)}
        </aside>
        <div className="category-branch-content">
          {activeRoot && <><header><div><small>دسته‌بندی اصلی</small><h2>{activeRoot.name_fa}</h2></div></header>
            <div className="category-branch-grid">{activeRoot.children.map((levelOne) => <section key={levelOne.id}><Link className="level-one-link" href={getCategoryUrl(levelOne, locale)} onClick={closeAll}>{levelOne.name_fa}<span className="category-direction-indicator" aria-hidden="true" /></Link>{levelOne.children.length > 0 && <div>{levelOne.children.map((leaf) => <Link key={leaf.id} href={getCategoryUrl(leaf, locale)} onClick={closeAll}>{leaf.name_fa}</Link>)}</div>}</section>)}</div>
            {!activeRoot.children.length && <div className="category-empty-branch"><p>این دسته زیرگروه دیگری ندارد.</p><Link href={getCategoryUrl(activeRoot, locale)} onClick={closeAll}>مشاهده محصولات</Link></div>}
            {activeRoot.children.length > 0 && <footer className="category-branch-footer"><Link href={getCategoryUrl(activeRoot, locale)} onClick={closeAll}>مشاهده همه محصولات این گروه ←</Link></footer>}
          </>}
        </div>
      </div>

      <div className="mobile-category-drawer">{mobileMode === "categories" && <><header><button type="button" onClick={mobileGoBack} aria-label={locale === "en" ? "Back" : "بازگشت"}><span aria-hidden="true">→</span><span className="mobile-category-back-label">{locale === "en" ? "Back" : "بازگشت"}</span></button><b>{mobileTitle || (locale === "en" ? "Categories" : "دسته‌بندی محصولات")}</b><button type="button" onClick={closeAll} aria-label={locale === "en" ? "Close menu" : "بستن منو"}>✕</button></header><div className="mobile-category-list" role="list">{loading && <p className="category-menu-state">{locale === "en" ? "Loading categories…" : "در حال دریافت دسته‌بندی‌ها…"}</p>}{!loading && !mobileLevel.length && <p className="category-menu-state">{locale === "en" ? "No categories found." : "دسته‌بندی‌ای یافت نشد."}</p>}{mobileLevel.map((node) => <div key={node.id} role="listitem"><Link href={getCategoryUrl(node, locale)} onClick={(event) => mobileDrill(node, event)}><span>{node.name_fa}</span>{node.product_count > 0 && <small>{formatNumber(node.product_count)}</small>}</Link><Link href={getCategoryUrl(node, locale)} onClick={closeAll} aria-label={`${locale === "en" ? "View" : "مشاهده"} ${node.name_fa}`}><span className="category-direction-indicator" aria-hidden="true" /></Link></div>)}</div></>}<Link className="mobile-category-index-link" href={`/${locale}/categories`} onClick={closeAll}>{locale === "en" ? "Browse all product categories" : "مشاهده همه دسته‌بندی‌های محصولات"}<span aria-hidden="true">←</span></Link></div>
    </section>}
  </nav>;
}
