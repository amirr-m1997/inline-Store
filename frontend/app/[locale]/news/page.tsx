import type { Metadata } from "next";
import Link from "next/link";
import { EditorialCard, EditorialPagination, EditorialTypeNav, editorialTypes, isDemoArticle, newsTypes } from "../../../components/content/editorial";
import { getArticlesServer, type EditorialArticlePage } from "../../../lib/api/content";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type PageProps = { params: Promise<{ locale: string }>; searchParams: Promise<{ type?: string | string[]; page?: string | string[] }> };
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] : value || "";
const emptyPage: EditorialArticlePage = { count: 0, next: null, previous: null, results: [] };
async function fetchType(type: string, parameters: Record<string, string | number | boolean | undefined> = {}) { return getArticlesServer<EditorialArticlePage>({ ...parameters, content_type: type, page_size: 12 }).catch(() => emptyPage); }

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params; const english = locale === "en"; const path = "/news"; const title = english ? "News & Events" : "اخبار و رویدادها"; const description = english ? "Published Mehrasl company news, events and product announcements." : "اخبار شرکت، رویدادها و معرفی‌های منتشرشده مهراصل.";
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: english ? "en_US" : "fa_IR", type: "website" } };
}

export default async function NewsPage({ params, searchParams }: PageProps) {
  const { locale } = await params; const query = await searchParams; const selected = valueOf(query.type); const type = newsTypes.has(selected) ? selected : ""; const pageNumber = Math.max(1, Number.parseInt(valueOf(query.page), 10) || 1);
  const pages = type ? [await fetchType(type, { page: pageNumber })] : await Promise.all(Array.from(newsTypes, (item) => fetchType(item, { page: pageNumber })));
  const articles = pages.flatMap((page) => page.results).sort((a, b) => Number(isDemoArticle(a)) - Number(isDemoArticle(b)) || new Date(b.published_at || 0).getTime() - new Date(a.published_at || 0).getTime());
  const unique = articles.filter((article, index, all) => all.findIndex((item) => item.id === article.id) === index);
  const english = locale === "en";
  return <main className="editorial-center site-container">
    <nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "News & Events" : "اخبار و رویدادها"}</b></nav>
    <header className="editorial-hero editorial-hero--news"><span>{english ? "Company newsroom" : "اتاق خبر شرکت"}</span><h1>{english ? "News & Events" : "اخبار و رویدادها"}</h1><p>{english ? "Company updates, events and product announcements from the editorial platform." : "خبرها، رویدادها و معرفی‌های محصول از بستر محتوای تحریریه."}</p></header>
    <EditorialTypeNav locale={locale} basePath={`/${locale}/news`} selectedType={type} allowedTypes={newsTypes} />
    {unique.length > 0 ? <section className="editorial-latest editorial-news-list" aria-labelledby="news-list-title"><header><div><span>{english ? "Published updates" : "به‌روزرسانی‌های منتشرشده"}</span><h2 id="news-list-title">{type ? (editorialTypes.find((item) => item.value === type)?.[english ? "en" : "fa"] || "") : (english ? "Latest news and events" : "جدیدترین اخبار و رویدادها")}</h2></div><span className="editorial-result-count">{unique.length.toLocaleString(english ? "en-US" : "fa-IR")}</span></header><div className="editorial-card-grid">{unique.map((article) => <EditorialCard key={article.id} article={article} locale={locale} />)}</div></section> : <div className="editorial-empty"><h2>{english ? "No published news is available yet." : "هنوز خبر منتشرشده‌ای در دسترس نیست."}</h2><p>{english ? "New company updates will appear here when published." : "خبرهای جدید شرکت پس از انتشار در این بخش نمایش داده می‌شوند."}</p></div>}
    <EditorialPagination locale={locale} basePath={`/${locale}/news`} page={pageNumber} hasNext={pages.some((item) => Boolean(item.next))} query={type ? { type } : undefined} />
  </main>;
}
