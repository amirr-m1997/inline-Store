import type { Metadata } from "next";
import { cache } from "react";
import { EnterpriseHome, type HomepageInitialData } from "../../components/catalog/enterprise-home";
import { getAdvantagesServer, getArticlesServer, getCapabilitiesServer, getCompanyServer, getHeroServer, getIndustriesServer, getSupplyBrandsServer, type EditorialArticlePage } from "../../lib/api/content";
import { getCategoryRootsServer, getProductsServer } from "../../lib/api/products";
import type { CompanyInfo, SiteHero } from "../../types/api";
import type { CatalogProduct } from "../../components/catalog/product-card";
import type { NavCategory } from "../../components/catalog/mega-menu";
import type { Advantage } from "../../components/catalog/company-advantages";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../lib/locale-url";

type HomepageData = HomepageInitialData & { company: CompanyInfo | null };
type PageProps = { params: Promise<{ locale: string }> };
const origin = () => process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const getHomepageCompany = cache(() => getCompanyServer<CompanyInfo>().catch(() => null));
const getHomepageHero = cache(() => getHeroServer<SiteHero>().catch(() => null));

async function loadHomepageData(locale: string): Promise<HomepageData> {
  const [company, hero, advantages, categories, featured, newest, discounted, brands, industries, capabilities, editorialPage] = await Promise.all([
    getHomepageCompany(),
    getHomepageHero(),
    getAdvantagesServer<Advantage[]>().catch(() => []),
    getCategoryRootsServer<NavCategory[]>().catch(() => []),
    getProductsServer({ featured: true, page_size: 8 }).then((data) => data.results).catch(() => []),
    getProductsServer({ ordering: "-created_at", page_size: 8 }).then((data) => data.results).catch(() => []),
    getProductsServer({ discounted: true, ordering: "-discount_percentage", page_size: 8 }).then((data) => data.results).catch(() => []),
    getSupplyBrandsServer<HomepageInitialData["brands"]>().catch(() => []),
    getIndustriesServer<HomepageInitialData["industries"]>().catch(() => []),
    getCapabilitiesServer<HomepageInitialData["capabilities"]>().catch(() => []),
    getArticlesServer<EditorialArticlePage>({ page_size: 3, ordering: "-published_at" }).catch(() => ({ count: 0, next: null, previous: null, results: [] })),
  ]);
  return { locale, company, hero, advantages, categories, featured, newest, discounted, brands, industries, capabilities, editorial: editorialPage.results };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const [company, hero] = await Promise.all([getHomepageCompany(), getHomepageHero()]);
  const name = company?.name_fa || hero?.title || (locale === "en" ? "Industrial Store" : "فروشگاه صنعتی");
  const description = company?.description || undefined;
  const url = `${origin()}/${locale}`;
  return {
    title: name,
    description,
    alternates: { canonical: absoluteUrl(localizedPath(locale)), ...localizedAlternates() },
    openGraph: { title: name, description, url, locale: locale === "en" ? "en_US" : "fa_IR", type: "website" },
  };
}

function jsonLd(data: unknown) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }} />;
}

function itemList(name: string, products: CatalogProduct[], locale: string) {
  return { "@context": "https://schema.org", "@type": "ItemList", name, itemListElement: products.map((product, index) => ({ "@type": "ListItem", position: index + 1, name: product.name, url: absoluteUrl(localizedPath(locale, `/product/${encodeURIComponent(product.slug)}`)) })) };
}

export default async function Home({ params }: PageProps) {
  const { locale } = await params;
  const data = await loadHomepageData(locale);
  const company = data.company;
  const siteUrl = absoluteUrl(localizedPath(locale));
  const organization = company ? { "@context": "https://schema.org", "@type": "Organization", name: company.name_fa, description: company.description || undefined, url: absoluteUrl(company.website || localizedPath(locale)), logo: company.logo ? absoluteUrl(company.logo) : undefined, telephone: company.phone || company.mobile || undefined, email: company.email || undefined, address: company.address || undefined } : null;
  return <>
    {organization && jsonLd(organization)}
    {(company || data.hero) && jsonLd({ "@context": "https://schema.org", "@type": "WebSite", name: company?.name_fa || data.hero?.title, url: siteUrl })}
    {data.featured.length > 0 && jsonLd(itemList("محصولات منتخب", data.featured, locale))}
    <EnterpriseHome {...data} />
  </>;
}
