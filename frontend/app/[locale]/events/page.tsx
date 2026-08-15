import type { Metadata } from "next";
import Link from "next/link";
import { EditorialCard, EditorialPagination } from "../../../components/content/editorial";
import { getArticlesServer, type EditorialArticlePage } from "../../../lib/api/content";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type PageProps = { params: Promise<{ locale: string }>; searchParams: Promise<{ page?: string | string[] }> };
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] || "" : value || "";
const emptyPage: EditorialArticlePage = { count: 0, next: null, previous: null, results: [] };

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params; const english = locale === "en"; const path = "/events";
  const title = english ? "Events & Exhibitions" : "رویدادها و نمایشگاه‌ها";
  const description = english ? "Published company events and exhibition information from the Mehrasl editorial platform." : "اطلاعات رویدادها و نمایشگاه‌های منتشرشده در بستر محتوای مهراصل.";
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: english ? "en_US" : "fa_IR", type: "website" } };
}

export default async function EventsPage({ params, searchParams }: PageProps) {
  const { locale } = await params; const query = await searchParams; const pageNumber = Math.max(1, Number.parseInt(valueOf(query.page), 10) || 1); const english = locale === "en";
  const page = await getArticlesServer<EditorialArticlePage>({ content_type: "event", page: pageNumber, page_size: 12 }).catch(() => emptyPage);
  return <main className="editorial-center site-container"><nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><Link href={`/${locale}/knowledge`}>{english ? "Knowledge & News" : "دانش و اخبار"}</Link><span aria-hidden="true">/</span><b>{english ? "Events" : "رویدادها"}</b></nav><header className="editorial-hero"><span>{english ? "Company events" : "رویدادهای شرکت"}</span><h1>{english ? "Events & Exhibitions" : "رویدادها و نمایشگاه‌ها"}</h1><p>{english ? "Editorial event information appears here only when it has been published in the CMS." : "اطلاعات رویدادها فقط پس از انتشار در سامانه محتوا در این بخش نمایش داده می‌شود."}</p></header>{page.results.length ? <section className="editorial-latest" aria-labelledby="events-list-title"><header><div><span>{english ? "Published events" : "رویدادهای منتشرشده"}</span><h2 id="events-list-title">{english ? "Latest events" : "آخرین رویدادها"}</h2></div><span className="editorial-result-count">{page.count.toLocaleString(english ? "en-US" : "fa-IR")}</span></header><div className="editorial-card-grid">{page.results.map((article) => <EditorialCard key={article.id} article={article} locale={locale} />)}</div></section> : <div className="editorial-empty"><h2>{english ? "No published events are available yet." : "هنوز رویداد منتشرشده‌ای در دسترس نیست."}</h2><p>{english ? "Verified event information will appear here when published." : "اطلاعات تأییدشده رویداد پس از انتشار در این بخش نمایش داده می‌شود."}</p></div>}<EditorialPagination locale={locale} basePath={`/${locale}/events`} page={pageNumber} hasNext={Boolean(page.next)} /></main>;
}
