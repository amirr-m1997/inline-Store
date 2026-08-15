import type { Metadata } from "next";
import Link from "next/link";
import { SearchCategoryGroup, SearchEditorialGroup, SearchBrandGroup, SearchProductGroup, SearchFAQGroup, SearchGroupSummary } from "../../../components/search/search-results";
import { getSiteSearchServer, type SiteSearchResponse } from "../../../lib/api/search";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type Props = { params: Promise<{ locale: string }>; searchParams: Promise<{ q?: string | string[] }> };
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] || "" : value || "";
const empty: SiteSearchResponse = { query: "", products: [], categories: [], brands: [], articles: [], faqs: [], counts: { products: 0, categories: 0, brands: 0, articles: 0, faqs: 0 } };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params; const english = locale === "en"; const title = english ? "Search Results" : "نتایج جستجو"; const path = "/search";
  return { title, description: english ? "Search Mehrasl products, categories, brands and industrial knowledge." : "جست‌وجوی محصولات، دسته‌بندی‌ها، برندها و دانش صنعتی مهراصل.", robots: { index: false, follow: true }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) } };
}

export default async function SearchPage({ params, searchParams }: Props) {
  const { locale } = await params;
  const raw = valueOf((await searchParams).q);
  const query = raw.trim().slice(0, 120);
  const english = locale === "en";
  const data = query.length >= 2 ? await getSiteSearchServer(query, locale).catch(() => empty) : empty;
  const faqs = data.faqs || [];
  const groups = { products: data.products, categories: data.categories, brands: data.brands, articles: data.articles, faqs };
  const visibleResultCount = Object.values(groups).reduce((total, items) => total + items.length, 0);
  const hasResults = visibleResultCount > 0;

  return <main className="site-search-page site-container">
    <nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "Search" : "جست‌وجو"}</b></nav>
    <header className="site-search-heading">
      <h1>{query ? (english ? `Results for “${query}”` : `نتایج برای «${query}»`) : (english ? "Search" : "جست‌وجو")}</h1>
      {query.length >= 2 && <p className="site-search-count">{visibleResultCount.toLocaleString(english ? "en-US" : "fa-IR")} {english ? "results" : "نتیجه"}</p>}
    </header>
    {query.length < 2 ? <section className="site-search-empty site-search-empty-query" aria-live="polite"><h2>{english ? "Search from the header" : "جست‌وجو را از نوار بالای صفحه شروع کنید"}</h2></section> : hasResults ? <>
      <SearchGroupSummary groups={groups} locale={locale} />
      <div className="site-search-results"><SearchProductGroup products={data.products} locale={locale} query={query} /><SearchCategoryGroup categories={data.categories} locale={locale} /><SearchBrandGroup brands={data.brands} locale={locale} /><SearchEditorialGroup articles={data.articles} locale={locale} /><SearchFAQGroup faqs={faqs} locale={locale} /></div>
    </> : <section className="site-search-empty" aria-live="polite"><h2>{english ? `No results for “${query}”` : `نتیجه‌ای برای «${query}» پیدا نشد.`}</h2><div className="site-search-empty-links"><Link href={`/${locale}/shop`}>{english ? "All products" : "همه محصولات"}</Link><Link href={`/${locale}/knowledge`}>{english ? "Knowledge & News" : "دانش و اخبار"}</Link><Link href={`/${locale}/categories`}>{english ? "Product categories" : "دسته‌بندی محصولات"}</Link></div></section>}
  </main>;
}
