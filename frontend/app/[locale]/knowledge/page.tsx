import type { Metadata } from "next";
import Link from "next/link";
import { EditorialCard, EditorialCategoryList, EditorialPagination, EditorialTypeNav, editorialTypes, FAQList } from "../../../components/content/editorial";
import { getArticlesServer, getEditorialCategoriesServer, getFAQsServer, type EditorialArticlePage } from "../../../lib/api/content";
import type { EditorialArticle, EditorialCategory, FAQEntry } from "../../../types/api";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type PageProps = { params: Promise<{ locale: string }>; searchParams: Promise<{ type?: string | string[]; category?: string | string[]; page?: string | string[] }> };
const validTypes: Set<string> = new Set(editorialTypes.map((item) => item.value).filter(Boolean));
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] : value || "";
const emptyPage: EditorialArticlePage = { count: 0, next: null, previous: null, results: [] };

async function articles(parameters: Record<string, string | number | boolean | undefined>) { return getArticlesServer<EditorialArticlePage>(parameters).catch(() => emptyPage); }

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const english = locale === "en";
  const path = "/knowledge";
  const title = english ? "Knowledge & News" : "دانش و اخبار";
  const description = english ? "Industrial news, technical knowledge, product guides and selection guidance from Mehrasl." : "اخبار صنعتی، دانش فنی، راهنماهای محصول و راهنمای انتخاب از مهراصل.";
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: english ? "en_US" : "fa_IR", type: "website" } };
}

export default async function KnowledgePage({ params, searchParams }: PageProps) {
  const { locale } = await params;
  const query = await searchParams;
  const selectedType = valueOf(query.type);
  const selectedCategory = valueOf(query.category);
  const pageNumber = Math.max(1, Number.parseInt(valueOf(query.page), 10) || 1);
  const type = validTypes.has(selectedType) ? selectedType : "";
  const filters = { page: pageNumber, page_size: 12, ...(type ? { content_type: type } : {}), ...(selectedCategory ? { category: selectedCategory } : {}) };
  const [page, featuredPage, categories, faqs] = await Promise.all([
    articles(filters),
    articles({ ...filters, page: 1, featured: true, page_size: 3 }),
    getEditorialCategoriesServer().catch(() => [] as EditorialCategory[]),
    getFAQsServer({}).then((items) => items.slice(0, 3)).catch(() => [] as FAQEntry[]),
  ]);
  const featured = featuredPage.results;
  const featuredIds = new Set(featured.map((article) => article.id));
  const latest = page.results.filter((article) => !featuredIds.has(article.id));
  const english = locale === "en";
  return <main className="editorial-center site-container">
    <nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "Knowledge & News" : "دانش و اخبار"}</b></nav>
    <header className="editorial-hero"><span>{english ? "Industrial editorial center" : "مرکز محتوای صنعتی"}</span><h1>{english ? "Knowledge & News" : "دانش و اخبار"}</h1><p>{english ? "A practical editorial view into industrial knowledge, products and company news." : "روایتی کاربردی از دانش صنعتی، محصولات و اخبار شرکت."}</p></header>
    <EditorialTypeNav locale={locale} basePath={`/${locale}/knowledge`} selectedType={type} /><p className="editorial-cross-link"><Link href={`/${locale}/resources`}>{english ? "Browse technical resources" : "مشاهده منابع فنی"} <span aria-hidden="true">←</span></Link><Link href={`/${locale}/search`}>{english ? "Search the site" : "جست‌وجو در سایت"} <span aria-hidden="true">←</span></Link></p>
    <EditorialCategoryList categories={categories} locale={locale} />
    {featured.length > 0 && <section className="editorial-featured" aria-labelledby="editorial-featured-title"><header><span>{english ? "Selected reading" : "مطالب منتخب"}</span><h2 id="editorial-featured-title">{english ? "Featured content" : "محتوای منتخب"}</h2></header><div className="editorial-featured-grid">{featured.slice(0, 3).map((article, index) => <EditorialCard key={article.id} article={article} locale={locale} variant={index === 0 ? "featured" : "standard"} />)}</div></section>}
    {latest.length > 0 && <section className="editorial-latest" aria-labelledby="editorial-latest-title"><header><div><span>{english ? "Latest from the center" : "تازه‌های مرکز"}</span><h2 id="editorial-latest-title">{type ? (editorialTypes.find((item) => item.value === type)?.[english ? "en" : "fa"] || (english ? "Latest content" : "تازه‌ترین مطالب")) : (english ? "Latest content" : "تازه‌ترین مطالب")}</h2></div><span className="editorial-result-count">{page.count.toLocaleString(english ? "en-US" : "fa-IR")}</span></header><div className="editorial-card-grid">{latest.map((article) => <EditorialCard key={article.id} article={article} locale={locale} />)}</div></section>}
    {!featured.length && !latest.length && <div className="editorial-empty"><h2>{english ? "No published content is available yet." : "هنوز محتوای منتشرشده‌ای در دسترس نیست."}</h2><p>{english ? "Please check back for new industrial knowledge and news." : "برای مشاهده دانش و اخبار جدید دوباره سر بزنید."}</p></div>}
    <EditorialPagination locale={locale} basePath={`/${locale}/knowledge`} page={pageNumber} hasNext={Boolean(page.next)} query={{ ...(type ? { type } : {}), ...(selectedCategory ? { category: selectedCategory } : {}) }} />
    <FAQList faqs={faqs} locale={locale} compact title={english ? "Common technical questions" : "پرسش‌های فنی متداول"} />
  </main>;
}
