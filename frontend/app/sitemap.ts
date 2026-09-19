import type { MetadataRoute } from "next";
import { absoluteUrl } from "../lib/locale-url";
import { getArticlesServer, getCapabilitiesServer, getIndustriesServer, type EditorialArticlePage } from "../lib/api/content";
import { getCategoryRootsServer, getProductBrandsServer, getProductsServer, type CategoryRecord, type ProductBrand } from "../lib/api/products";
import type { HomepageCapability, HomepageIndustry } from "../components/catalog/enterprise-home";

type SitemapEntry = MetadataRoute.Sitemap[number];

const STATIC_ROUTES = [
  { path: "", priority: 1.0, changeFrequency: "daily" as const },
  { path: "/shop", priority: 0.9, changeFrequency: "daily" as const },
  { path: "/categories", priority: 0.8, changeFrequency: "weekly" as const },
  { path: "/brands", priority: 0.8, changeFrequency: "weekly" as const },
  { path: "/capabilities", priority: 0.7, changeFrequency: "monthly" as const },
  { path: "/industries", priority: 0.7, changeFrequency: "monthly" as const },
  { path: "/about", priority: 0.7, changeFrequency: "monthly" as const },
  { path: "/contact", priority: 0.7, changeFrequency: "monthly" as const },
  { path: "/knowledge", priority: 0.7, changeFrequency: "weekly" as const },
  { path: "/faq", priority: 0.6, changeFrequency: "monthly" as const },
  { path: "/support/warranty", priority: 0.6, changeFrequency: "monthly" as const },
];

function localized(path: string, now: Date, priority: number, changeFrequency: SitemapEntry["changeFrequency"]): SitemapEntry[] {
  return (["fa", "en"] as const).map((locale) => ({ url: absoluteUrl(`/${locale}${path}`), lastModified: now, changeFrequency, priority }));
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const entries: MetadataRoute.Sitemap = STATIC_ROUTES.flatMap(({ path, priority, changeFrequency }) => localized(path, now, priority, changeFrequency));

  const [categories, brands, capabilities, industries, articles, products] = await Promise.all([
    getCategoryRootsServer<CategoryRecord[]>().catch(() => [] as CategoryRecord[]),
    getProductBrandsServer().catch(() => [] as ProductBrand[]),
    getCapabilitiesServer<HomepageCapability[]>().catch(() => [] as HomepageCapability[]),
    getIndustriesServer<HomepageIndustry[]>().catch(() => [] as HomepageIndustry[]),
    getArticlesServer<EditorialArticlePage>({ page_size: 100, ordering: "-published_at" }).catch(() => null),
    getProductsServer({ page_size: 500, ordering: "-updated_at" }).catch(() => null),
  ]);

  for (const category of categories) {
    if (category.slug) entries.push(...localized(`/category/${encodeURIComponent(category.slug)}`, now, 0.8, "weekly"));
  }
  for (const brand of brands) {
    if (brand.slug) entries.push(...localized(`/brands/${encodeURIComponent(brand.slug)}`, now, 0.7, "weekly"));
  }
  for (const capability of capabilities) {
    if (capability.slug) entries.push(...localized(`/capabilities/${encodeURIComponent(capability.slug)}`, now, 0.6, "monthly"));
  }
  for (const industry of industries) {
    if (industry.slug) entries.push(...localized(`/industries/${encodeURIComponent(industry.slug)}`, now, 0.6, "monthly"));
  }
  for (const article of articles?.results ?? []) {
    if (article.slug) entries.push(...localized(`/knowledge/${encodeURIComponent(article.slug)}`, now, 0.6, "monthly"));
  }
  for (const product of products?.results ?? []) {
    if (product.slug) entries.push(...localized(`/product/${encodeURIComponent(product.slug)}`, now, 0.8, "weekly"));
  }
  return entries;
}
