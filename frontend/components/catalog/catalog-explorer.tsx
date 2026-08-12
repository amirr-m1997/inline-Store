"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getCategorySearchUrl, getCategoryUrl } from "../../lib/category-url";
import { CategoryChevron } from "./category-chevron";
import type { NavCategory } from "./mega-menu";
import { ProductCard, ProductCardSkeleton, type CatalogProduct } from "./product-card";

type ProductPage = { count: number; results: CatalogProduct[] };
type TreeCategory = NavCategory & { children: TreeCategory[]; product_count: number };
type CategoryResponse = NavCategory & { redirect_slug?: string };
const pageSize = 12;

function branchContains(node: TreeCategory, slug: string): boolean { return node.slug === slug || node.children.some((child) => branchContains(child, slug)); }
function findCategory(nodes: TreeCategory[], slug: string): TreeCategory | null { for (const node of nodes) { if (node.slug === slug) return node; const found = findCategory(node.children, slug); if (found) return found; } return null; }

function TreeBranch({ node, activeSlug, locale, depth = 0 }: { node: TreeCategory; activeSlug: string; locale: string; depth?: number }) {
  const activePath = branchContains(node, activeSlug);
  const [open, setOpen] = useState(activePath);
  useEffect(() => { if (activePath) setOpen(true); }, [activePath]);
  return <div className="catalog-tree-node" style={{ "--tree-depth": depth } as React.CSSProperties}><div className="catalog-tree-row">{node.children.length > 0 ? <button type="button" onClick={() => setOpen((value) => !value)} aria-label={`${open ? "بستن" : "نمایش"} زیرگروه‌های ${node.name_fa}`} aria-expanded={open}><CategoryChevron open={open} locale={locale} /></button> : <span className="catalog-tree-spacer" />}<Link className={node.slug === activeSlug ? "active" : ""} href={getCategoryUrl(node, locale)} aria-current={node.slug === activeSlug ? "page" : undefined}>{node.name_fa}</Link></div>{open && node.children.length > 0 && <div className="catalog-tree-children">{node.children.map((child) => <TreeBranch key={child.id} node={child} activeSlug={activeSlug} locale={locale} depth={depth + 1} />)}</div>}</div>;
}

export function CatalogExplorer({ slug, query }: { slug: string; query?: string }) {
  const router = useRouter();
  const routeParams = useParams<{ locale: string }>();
  const locale = routeParams.locale || "fa";
  const isSearch = slug === "search";
  const isShop = slug === "shop";
  const isNewest = slug === "newest";
  const isBestDiscounts = slug === "best-discounts";
  const isSpecialListing = isNewest || isBestDiscounts;
  const [roots, setRoots] = useState<TreeCategory[]>([]);
  const [category, setCategory] = useState<NavCategory | null>(null);
  const [categoryStatus, setCategoryStatus] = useState<"loading" | "resolved" | "not_found" | "error">(isSearch || isShop || isSpecialListing ? "resolved" : "loading");
  const [products, setProducts] = useState<ProductPage | null>(null);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [productsError, setProductsError] = useState(false);
  const [page, setPage] = useState(1);
  const [inStock, setInStock] = useState(false);
  const [ordering, setOrdering] = useState(isNewest ? "-created_at" : isBestDiscounts ? "-discount_percentage" : "code");

  useEffect(() => { fetch("/api/v1/categories/tree/").then((response) => { if (!response.ok) throw new Error(); return response.json(); }).then(setRoots).catch(() => setRoots([])); }, []);
  useEffect(() => {
    setPage(1); setProducts(null);
    if (isSearch || isShop || isSpecialListing) { setCategory(null); setCategoryStatus("resolved"); return; }
    setCategory(null); setCategoryStatus("loading");
    fetch(`/api/v1/categories/by-slug/${encodeURIComponent(slug)}/`)
      .then(async (response) => { if (response.status === 404) { setCategoryStatus("not_found"); return null; } if (!response.ok) throw new Error(); const data = await response.json() as CategoryResponse; if (data.redirect_slug) router.replace(getCategoryUrl(data, locale)); setCategoryStatus("resolved"); return data; })
      .then(setCategory)
      .catch(() => { setCategory(null); setCategoryStatus("error"); });
  }, [isSearch, isShop, isSpecialListing, locale, router, slug]);
  useEffect(() => {
    if (isNewest) setOrdering("-created_at");
    else if (isBestDiscounts) setOrdering("-discount_percentage");
  }, [isBestDiscounts, isNewest]);
  useEffect(() => {
    if (!isSearch && !isShop && !isSpecialListing && (categoryStatus !== "resolved" || !category)) { setLoadingProducts(categoryStatus === "loading"); setProducts(null); return; }
    const parameters = new URLSearchParams({ page: String(page), page_size: String(pageSize), ordering });
    if ((isSearch || isShop) && query?.trim()) parameters.set("search", query.trim());
    else if (category) parameters.set("category", String(category.id));
    if (inStock) parameters.set("in_stock", "true");
    if (isBestDiscounts) parameters.set("discounted", "true");
    setLoadingProducts(true); setProductsError(false);
    fetch(`/api/v1/products/?${parameters}`).then((response) => { if (!response.ok) throw new Error(); return response.json(); }).then(setProducts).catch(() => { setProducts(null); setProductsError(true); }).finally(() => setLoadingProducts(false));
  }, [category, categoryStatus, inStock, isBestDiscounts, isSearch, isShop, isSpecialListing, ordering, page, query]);

  const title = isShop ? "همه محصولات" : isNewest ? "جدیدترین‌ها" : isBestDiscounts ? "بیشترین تخفیف" : isSearch ? "جست‌وجوی کاتالوگ" : categoryStatus === "loading" ? "در حال دریافت دسته‌بندی…" : categoryStatus === "error" ? "خطا در دریافت دسته‌بندی" : category?.name_fa || "دسته‌بندی یافت نشد";
  const totalPages = Math.max(1, Math.ceil((products?.count ?? 0) / pageSize));
  const search = (value: string) => { setPage(1); router.push(isShop ? `/${locale}/shop?q=${encodeURIComponent(value)}` : getCategorySearchUrl(locale, value)); };
  const activeTreeNode = findCategory(roots, slug);

  return <main className="catalog-experience site-container"><div className="catalog-breadcrumb"><Link href={`/${locale}`}>خانه</Link><span>‹</span><span>{title}</span></div><div className="catalog-shell"><aside className="catalog-sidebar"><div className="catalog-side-title">درخت دسته‌بندی‌ها</div>{roots.map((root) => <TreeBranch key={root.id} node={root} activeSlug={slug} locale={locale} />)}</aside><section className="catalog-content"><header><div><p>کاتالوگ صنعتی</p><h1>{title}</h1><span>{(products?.count ?? 0).toLocaleString("fa-IR")} محصول</span></div></header>
    <div className="catalog-filters"><label><span>جست‌وجوی فنی</span><input defaultValue={query} placeholder="نام، SKU یا کد فنی" onKeyDown={(event) => { if (event.key === "Enter") search(event.currentTarget.value); }} /></label><label><span>مرتب‌سازی</span><select value={ordering} onChange={(event) => { setOrdering(event.target.value); setPage(1); }}><option value="code">کد کالا</option><option value="name">نام کالا</option><option value="-created_at">جدیدترین</option></select></label><label className="stock-filter"><input type="checkbox" checked={inStock} onChange={(event) => { setInStock(event.target.checked); setPage(1); }} /> فقط موجود</label><button className="spec-filter" type="button">مشخصات فنی</button></div>
    {activeTreeNode && activeTreeNode.children.length > 0 && <div className="catalog-children">{activeTreeNode.children.map((child) => <Link key={child.id} href={getCategoryUrl(child, locale)}>{child.name_fa}</Link>)}</div>}
    {categoryStatus === "not_found" ? <div className="empty-state"><b>دسته‌بندی یافت نشد</b><p>نشانی این دسته‌بندی معتبر نیست یا دسته غیرفعال شده است.</p></div> : categoryStatus === "error" || productsError ? <div className="empty-state catalog-api-error"><b>دریافت اطلاعات ناموفق بود</b><p>ارتباط با سرویس کاتالوگ برقرار نشد. لطفاً دوباره تلاش کنید.</p></div> : loadingProducts ? <div className="industrial-product-grid catalog-card-grid">{Array.from({ length: 8 }).map((_, i) => <ProductCardSkeleton key={i} />)}</div> : !products?.results.length ? <div className="empty-state"><b>محصولی موجود نیست</b><p>{isBestDiscounts ? "در حال حاضر محصول تخفیف‌داری وجود ندارد." : isShop || isNewest ? "محصول فعالی در فروشگاه ثبت نشده است." : "در این دسته‌بندی محصول فعالی ثبت نشده است."}</p></div> : <div className="industrial-product-grid catalog-card-grid">{products.results.map((product) => <ProductCard key={product.id} product={product} />)}</div>}
    {(products?.count ?? 0) > pageSize && <div className="catalog-pagination"><button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>صفحه قبل</button><span>{page.toLocaleString("fa-IR")} از {totalPages.toLocaleString("fa-IR")}</span><button disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>صفحه بعد</button></div>}
  </section></div></main>;
}
