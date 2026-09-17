import type { CatalogQueryResponse, CategoryRecord } from "./api/products";
import { getCatalogQueryServer, getCategoryServer } from "./api/products";
import { absoluteUrl, localizedAlternates, localizedPath } from "./locale-url";

export type CatalogRouteSearch = Record<string, string | string[] | undefined>;
export type CatalogInitialContext = { category: (CategoryRecord & { redirect_slug?: string }) | null; data: CatalogQueryResponse };

function first(value: string | string[] | undefined) { return Array.isArray(value) ? value[0] : value; }

export async function loadCatalogInitial(slug: string, searchParams: CatalogRouteSearch): Promise<CatalogInitialContext> {
  const isSpecial = slug === "shop" || slug === "newest" || slug === "best-discounts" || slug === "search";
  const category = isSpecial ? null : await getCategoryServer(slug);
  const parameters: Record<string, string | number | boolean | undefined> = { page_size: 12 };
  for (const [key, value] of Object.entries(searchParams)) {
    const normalized = first(value);
    if (normalized !== undefined && (key === "q" || key === "brand" || key === "availability" || key === "ordering" || key === "sort" || key === "page" || key === "cursor" || key === "in_stock" || key === "has_image" || key === "discounted" || key === "featured" || key === "condition" || key === "price_min" || key === "price_max" || key.startsWith("attr_"))) parameters[key] = normalized;
  }
  if (!parameters.category && category) parameters.category = category.id;
  if (slug === "newest") parameters.ordering = parameters.ordering || "-created_at";
  if (slug === "best-discounts") { parameters.ordering = parameters.ordering || "-discount_percentage"; parameters.discounted = "1"; }
  return { category, data: await getCatalogQueryServer(parameters) };
}

export function catalogTitle(slug: string, category: CategoryRecord | null, locale = "fa") {
  const english = locale === "en";
  if (slug === "shop") return english ? "All products" : "همه محصولات";
  if (slug === "newest") return english ? "Newest products" : "جدیدترین‌ها";
  if (slug === "best-discounts") return english ? "Best discounts" : "بیشترین تخفیف";
  if (slug === "search") return english ? "Catalog search" : "جست‌وجوی کاتالوگ";
  if (category) return category.name_fa;
  return english ? "Product catalog" : "کاتالوگ محصولات";
}

export function catalogMetadata(slug: string, locale: string, category: CategoryRecord | null, searchParams: CatalogRouteSearch) {
  const title = catalogTitle(slug, category, locale);
  const english = locale === "en";
  const hasQueryState = Object.keys(searchParams).length > 0;
  const path = category ? `/category/${slug}` : `/${slug}`;
  const description = category ? (english ? `Products in ${catalogTitle(slug, category, locale)}` : `محصولات ${category.name_fa}`) : title;
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, robots: hasQueryState ? { index: false, follow: true } : { index: true, follow: true } };
}

export function catalogStructuredData(slug: string, locale: string, category: CategoryRecord | null, data: CatalogQueryResponse) {
  const title = catalogTitle(slug, category, locale);
  const home = locale === "en" ? "Home" : "خانه";
  const items = data.products.map((product, index) => ({ "@type": "ListItem", position: index + 1, url: absoluteUrl(localizedPath(locale, `/product/${product.slug}`)), name: product.name }));
  const breadcrumb = [{ "@type": "ListItem", position: 1, name: home, item: absoluteUrl(localizedPath(locale)) }, ...(category ? [{ "@type": "ListItem", position: 2, name: category.name_fa, item: absoluteUrl(localizedPath(locale, `/category/${category.slug}`)) }] : [])];
  return [{ "@context": "https://schema.org", "@type": "ItemList", name: title, numberOfItems: items.length, itemListElement: items }, { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: breadcrumb }];
}

