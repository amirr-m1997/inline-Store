"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { getCategoryUrl } from "../../lib/category-url";

type NavigationItem = { id: number; title_fa: string; url: string; icon: string };
export type CategoryTreeNode = { id: number; code: string; name_fa: string; name_en: string; slug: string; level: number; product_count: number; children: CategoryTreeNode[] };
type CategoryNavigationProps = { mobileOpen: boolean; onNavigate: () => void };

function asArray<T>(data: unknown): T[] { return Array.isArray(data) ? data as T[] : []; }

export function CategoryNavigation({ mobileOpen, onNavigate }: CategoryNavigationProps) {
  const { locale = "fa" } = useParams<{ locale: string }>();
  const navigationRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [items, setItems] = useState<NavigationItem[]>([]);
  const [roots, setRoots] = useState<CategoryTreeNode[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeRootId, setActiveRootId] = useState<number | null>(null);
  const [mobilePath, setMobilePath] = useState<CategoryTreeNode[]>([]);

  useEffect(() => {
    fetch("/api/v1/site/navigation/").then((response) => response.ok ? response.json() : []).then((data) => setItems(asArray<NavigationItem>(data))).catch(() => setItems([]));
  }, []);
  const loadTree = () => {
    if (roots.length || loading) return;
    setLoading(true);
    fetch("/api/v1/categories/tree/")
      .then((response) => response.ok ? response.json() : [])
      .then((data) => { const tree = asArray<CategoryTreeNode>(data); setRoots(tree); setActiveRootId(tree[0]?.id ?? null); })
      .catch(() => setRoots([])).finally(() => setLoading(false));
  };
  const toggleCategories = () => { setOpen((current) => { const next = !current; if (next) loadTree(); else setMobilePath([]); return next; }); };
  const closeCategories = () => { setOpen(false); setMobilePath([]); };
  const closeAll = () => { closeCategories(); onNavigate(); };

  useEffect(() => {
    if (!mobileOpen) closeCategories();
  }, [mobileOpen]);
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => { if (!navigationRef.current?.contains(event.target as Node)) closeCategories(); };
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") { closeCategories(); triggerRef.current?.focus(); } };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => { document.removeEventListener("pointerdown", onPointerDown); document.removeEventListener("keydown", onKeyDown); };
  }, [open]);

  const ordinaryItems = useMemo(() => items.filter((item) => {
    const normalizedUrl = item.url.replace(/\/$/, "");
    return !normalizedUrl.includes("/categor")
      && !item.title_fa.includes("دسته‌بندی")
      && normalizedUrl !== "/fa/shop"
      && item.title_fa !== "فروشگاه";
  }), [items]);
  const homeItems = ordinaryItems.filter((item) => item.url.replace(/\/$/, "") === "/fa" || item.title_fa === "صفحه اصلی");
  const remainingItems = ordinaryItems.filter((item) => !homeItems.includes(item));
  const activeRoot = roots.find((root) => root.id === activeRootId) ?? roots[0];
  const mobileParent = mobilePath.at(-1);
  const mobileNodes = mobileParent ? mobileParent.children : roots;

  return <nav ref={navigationRef} className={`reference-category-nav site-container${mobileOpen ? " mobile-open" : ""}`} aria-label="ناوبری وب‌سایت">
    <div className="reference-nav-links">
      <button ref={triggerRef} className="category-menu-trigger" type="button" onClick={toggleCategories} aria-expanded={open} aria-controls="product-category-menu"><span aria-hidden="true">☰</span><b>دسته‌بندی محصولات</b><i aria-hidden="true">⌄</i></button>
      {homeItems.map((item) => <Link key={item.id} href={item.url} onClick={closeAll}>{item.icon && <span>{item.icon}</span>}{item.title_fa}</Link>)}
      <Link href="/fa/shop" onClick={closeAll}>همه محصولات</Link>
      <Link href="/fa/newest" onClick={closeAll}>جدیدترین‌ها</Link>
      <Link href="/fa/best-discounts" onClick={closeAll}>بیشترین تخفیف</Link>
      {remainingItems.map((item) => <Link key={item.id} href={item.url} onClick={closeAll}>{item.icon && <span>{item.icon}</span>}{item.title_fa}</Link>)}
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
        <header><button type="button" onClick={() => mobilePath.length ? setMobilePath((path) => path.slice(0, -1)) : closeCategories()} aria-label={mobilePath.length ? "بازگشت به سطح قبل" : "بستن دسته‌بندی‌ها"}>{mobilePath.length ? "→" : "×"}</button><div><small>{mobilePath.length ? "زیرگروه‌های" : "فهرست"}</small><b>{mobileParent?.name_fa ?? "دسته‌بندی محصولات"}</b></div>{mobileParent ? <Link href={getCategoryUrl(mobileParent, locale)} onClick={closeAll}>همه</Link> : <span />}</header>
        <div className="mobile-category-list">{loading && <p className="category-menu-state">در حال دریافت دسته‌بندی‌ها…</p>}{mobileNodes.map((node) => <div key={node.id}><Link href={getCategoryUrl(node, locale)} onClick={closeAll}>{node.name_fa}<small>{node.product_count.toLocaleString("fa-IR")} محصول</small></Link>{node.children.length > 0 && <button type="button" onClick={() => setMobilePath((path) => [...path, node])} aria-label={`نمایش زیرگروه‌های ${node.name_fa}`}><span className="category-direction-indicator" aria-hidden="true" /></button>}</div>)}</div>
      </div>
    </section>}
  </nav>;
}
