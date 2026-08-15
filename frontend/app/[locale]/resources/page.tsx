import type { Metadata } from "next";
import Link from "next/link";
import { getProductDocumentsServer, type ProductResource, type ProductResourcePage } from "../../../lib/api/products";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type PageProps = { params: Promise<{ locale: string }>; searchParams: Promise<{ type?: string | string[]; language?: string | string[]; q?: string | string[] }> };
const valueOf = (value?: string | string[]) => Array.isArray(value) ? value[0] || "" : value || "";
const emptyPage: ProductResourcePage = { count: 0, next: false, previous: false, results: [] };
const typeOptions = ["datasheet", "manual", "cad", "certificate", "catalogue", "other"] as const;

function documentTypeLabel(type: ProductResource["type"], english: boolean) {
  const labels = { datasheet: english ? "Datasheet" : "دیتاشیت", manual: english ? "Manual" : "راهنما", cad: "CAD", certificate: english ? "Certificate" : "گواهی‌نامه", catalogue: english ? "Catalogue" : "کاتالوگ", other: english ? "Other" : "سایر" };
  return labels[type] || type;
}

function formatSize(size: number, english: boolean) {
  if (!size) return "";
  const units = ["B", "KB", "MB", "GB"];
  let value = size; let index = 0;
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
  return `${value >= 10 || index === 0 ? Math.round(value) : value.toFixed(1)} ${units[index]}`;
}

async function loadResources(parameters: Record<string, string | undefined>) {
  return getProductDocumentsServer({ ...parameters, page: "1", page_size: "24" }).catch(() => emptyPage);
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params; const english = locale === "en"; const path = "/resources";
  const title = english ? "Technical Resources" : "منابع فنی";
  const description = english ? "Published datasheets, manuals, certificates, catalogues and technical files for products." : "دیتاشیت‌ها، راهنماها، گواهی‌ها، کاتالوگ‌ها و فایل‌های فنی منتشرشده محصولات.";
  return { title, description, robots: { index: true, follow: true }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, url: absoluteUrl(localizedPath(locale, path)), locale: english ? "en_US" : "fa_IR", type: "website" } };
}

export default async function ResourcesPage({ params, searchParams }: PageProps) {
  const { locale } = await params; const query = await searchParams; const type = valueOf(query.type); const language = valueOf(query.language); const search = valueOf(query.q).trim();
  const page = await loadResources({ ...(typeOptions.includes(type as typeof typeOptions[number]) ? { type } : {}), ...(language ? { language } : {}), ...(search ? { q: search } : {}) });
  const english = locale === "en";
  const filteredQuery = (nextType = type, nextLanguage = language) => { const params = new URLSearchParams(); if (nextType) params.set("type", nextType); if (nextLanguage) params.set("language", nextLanguage); if (search) params.set("q", search); return params.toString() ? `?${params}` : ""; };
  const jsonLd = page.results.length ? { "@context": "https://schema.org", "@type": "ItemList", name: english ? "Technical resources" : "منابع فنی", itemListElement: page.results.map((resource, index) => ({ "@type": "ListItem", position: index + 1, name: resource.title, url: resource.file_url })) } : null;
  return <><main className="public-page site-container">
    <nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "Technical Resources" : "منابع فنی"}</b></nav>
    <header className="content-index-heading"><span>{english ? "Product documentation" : "مستندات محصولات"}</span><h1>{english ? "Technical Resources" : "منابع فنی"}</h1><p>{english ? "Find approved technical documents by type, language and product context." : "مدارک فنی تأییدشده را بر اساس نوع، زبان و محصول پیدا کنید."}</p></header>
    <form className="resource-filters" method="get" aria-label={english ? "Resource filters" : "فیلتر منابع فنی"}><label>{english ? "Search" : "جستجو"}<input name="q" defaultValue={search} placeholder={english ? "Title, file or product code" : "عنوان، فایل یا کد محصول"} /></label><label>{english ? "Type" : "نوع سند"}<select name="type" defaultValue={type}><option value="">{english ? "All types" : "همه انواع"}</option>{typeOptions.map((item) => <option key={item} value={item}>{documentTypeLabel(item, english)}</option>)}</select></label><label>{english ? "Language" : "زبان"}<input name="language" defaultValue={language} placeholder={english ? "e.g. en/fa" : "مثلاً en/fa"} /></label><button className="btn-secondary" type="submit">{english ? "Apply" : "اعمال"}</button>{(type || language || search) && <Link className="resource-filter-reset" href={`/${locale}/resources`}>{english ? "Clear" : "پاک‌کردن"}</Link>}</form>
    <nav className="resource-cross-links" aria-label={english ? "Related destinations" : "مسیرهای مرتبط"}><Link href={`/${locale}/knowledge`}>{english ? "Knowledge & News" : "دانش و اخبار"}</Link><Link href={`/${locale}/support`}>{english ? "Customer Service" : "امور مشتریان"}</Link></nav>
    {page.results.length ? <><p className="resource-result-count">{page.count.toLocaleString(english ? "en-US" : "fa-IR")} {english ? "resources" : "منبع"}</p><div className="resource-list">{page.results.map((resource) => { const demo = resource.title.startsWith("[DEMO]") || resource.display_name.startsWith("[DEMO]"); const size = formatSize(resource.size, english); return <article className="resource-row" key={resource.id}><div className="resource-row-heading"><span className="resource-type">{documentTypeLabel(resource.type, english)}</span>{demo && <span className="content-demo-indicator">{english ? "Demo" : "نمونه"}</span>}<h2>{resource.title}</h2></div><p className="resource-product"><Link href={`/${locale}/product/${resource.product.slug}`}>{resource.product.name}</Link><br /><bdi dir="ltr">{resource.product.code}</bdi></p><dl className="resource-metadata">{resource.file_name && <div><dt>{english ? "File" : "فایل"}</dt><dd dir="ltr">{resource.file_name}</dd></div>}{resource.language && <div><dt>{english ? "Language" : "زبان"}</dt><dd dir="ltr">{resource.language}</dd></div>}{resource.revision && <div><dt>{english ? "Revision" : "ویرایش"}</dt><dd dir="ltr">{resource.revision}</dd></div>}{size && <div><dt>{english ? "Size" : "حجم"}</dt><dd dir="ltr">{size}</dd></div>}</dl><a className="btn-secondary" href={resource.file_url} download={resource.file_name || undefined} target="_blank" rel="noreferrer" aria-label={`${english ? "Download" : "دانلود"} ${resource.title}`}>{english ? "Download" : "دانلود"}</a></article>; })}</div>{(page.next || page.previous) && <nav className="resource-pagination" aria-label={english ? "Resource pagination" : "صفحه‌بندی منابع"}><span>{english ? "More resources are available." : "منابع بیشتری وجود دارد."}</span></nav>}</> : <p className="home-section-empty">{search || type || language ? (english ? "No resources match these filters." : "منبعی با این فیلترها پیدا نشد.") : (english ? "No published technical resources are available." : "منبع فنی منتشرشده‌ای در دسترس نیست.")}</p>}
  </main>{jsonLd && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />}</>;
}
