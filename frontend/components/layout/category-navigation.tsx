"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";
import { getCategories } from "../../lib/api/products";
import { getNavigation } from "../../lib/api/content";

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
  const [mobilePath, setMobilePath] = useState<CategoryTreeNode[]>([]);
  const [mobileMode, setMobileMode] = useState<"main" | "categories">("main");

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
  const toggleCategories = () => { setMobileMode("categories"); setOpen((current) => { const next = !current; if (next) loadTree(); else setMobilePath([]); return next; }); };
  const closeCategories = () => { setOpen(false); setMobilePath([]); setMobileMode("main"); };
  const returnToMainMenu = () => { setOpen(false); setMobilePath([]); setMobileMode("main"); };
  const closeAll = () => { closeCategories(); onNavigate(); };

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
  const mobileParent = mobilePath.at(-1);
  const mobileNodes = mobileParent ? mobileParent.children : roots;

  return <nav id="site-mobile-navigation" ref={navigationRef} className={`reference-category-nav site-container${mobileOpen ? " mobile-open" : ""}${mobileMode === "categories" ? " category-mode" : ""}`} aria-label="ناوبری وب‌سایت">
    <div className="reference-nav-links">
      {(!mobileOpen || mobileMode === "main") && <><div className="category-nav-section"><span className="mobile-nav-section-label">دسته‌بندی محصولات</span><button ref={triggerRef} className="category-menu-trigger" type="button" onClick={toggleCategories} aria-expanded={open} aria-controls="product-category-menu"><span className="category-menu-icon" aria-hidden="true"><i /><i /><i /></span><b>دسته‌بندی محصولات</b><i aria-hidden="true">⌄</i></button></div>
      <div className="reference-primary-links">{homeItems.map((item) => <Link key={item.id} href={localizeUrl(item.url)} onClick={closeAll}>{item.icon && <span aria-hidden="true">{item.icon}</span>}{locale === "en" ? "Home" : "صفحه اصلی"}</Link>)}<Link href={`/${locale}/shop`} onClick={closeAll}>{locale === "en" ? "All products" : "همه محصولات"}</Link><Link href={`/${locale}/newest`} onClick={closeAll}>{locale === "en" ? "Latest" : "جدیدترین‌ها"}</Link><Link href={`/${locale}/best-discounts`} onClick={closeAll}>{locale === "en" ? "Best discounts" : "بیشترین تخفیف"}</Link><Link href={`/${locale}/support`} onClick={closeAll} aria-current={supportActive ? "page" : undefined}>{locale === "en" ? "Customer Service" : "امور مشتریان"}</Link>{remainingItems.map((item) => <Link key={item.id} href={localizeUrl(item.url)} onClick={closeAll}>{item.icon && <span aria-hidden="true">{item.icon}</span>}{item.title_fa}</Link>)}</div></>}
    </div>

    {open && <section id="product-category-menu" className="product-category-menu" aria-label="دسته‌بندی محصولات">
      <div className="desktop-category-menu">
        <aside aria-label="دسته‌بندی‌های اصلی">
          <header><b>گروه‌های اصلی</b><small>{roots.length.toLocaleString("fa-IR")} گروه</small></header>
          {loading && <p className="category-menu-state">در حال دریافت دسته‌بندی‌ها…</p>}
          {!loading && !roots.length && <p className="category-menu-state">دسته‌بندی‌ای یافت نشد.</p>}
          {roots.map((root) => <div className={`root-category-row${root.id === activeRoot?.id ? " active" : ""}`} key={root.id} onMouseEnter={() => setActiveRootId(root.id)}>
            <button type="button" onFocus={() => setActiveRootId(root.id)} onClick={() => setActiveRootId(root.id)} aria-pressed={root.id === activeRoot?.id}><span>{root.name_fa}</span><small>{root.product_count.toLocaleString("fa-IR")}</small></button>
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

      <div className="mobile-category-drawer">
        <header><button autoFocus type="button" onClick={() => mobilePath.length ? setMobilePath((path) => path.slice(0, -1)) : returnToMainMenu()} aria-label={mobilePath.length ? "بازگشت به سطح قبل" : "بازگشت به منوی اصلی"}><span aria-hidden="true">→</span><span className="mobile-category-back-label">بازگشت</span></button><div><small>{mobilePath.length ? "زیرگروه‌های" : "فهرست"}</small><b>{mobileParent?.name_fa ?? "دسته‌بندی محصولات"}</b></div>{mobileParent ? <Link href={getCategoryUrl(mobileParent, locale)} onClick={closeAll}>همه</Link> : <span />}</header>
        <div className="mobile-category-list">{loading && <p className="category-menu-state">در حال دریافت دسته‌بندی‌ها…</p>}{mobileNodes.map((node) => <div key={node.id}><Link href={getCategoryUrl(node, locale)} onClick={closeAll}>{node.name_fa}<small>{node.product_count.toLocaleString("fa-IR")} محصول</small></Link>{node.children.length > 0 && <button type="button" onClick={() => setMobilePath((path) => [...path, node])} aria-label={`نمایش زیرگروه‌های ${node.name_fa}`}><span className="category-direction-indicator" aria-hidden="true" /></button>}</div>)}</div>
      </div>
    </section>}
  </nav>;
}
