import type { Metadata } from "next";
import Link from "next/link";
import { getProductDocumentsServer, type ProductResource } from "../../../lib/api/products";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

async function loadResources() { return getProductDocumentsServer().catch(() => []); }

function documentTypeLabel(type: ProductResource["type"], english: boolean) {
  const labels = { datasheet: english ? "Datasheet" : "دیتاشیت", manual: english ? "Manual" : "راهنما", cad: "CAD", certificate: english ? "Certificate" : "گواهی‌نامه", other: english ? "Other" : "سایر" };
  return labels[type] || type;
}

function formatSize(size: number, english: boolean) {
  if (!size) return "";
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
  return `${value >= 10 || index === 0 ? Math.round(value) : value.toFixed(1)} ${units[index]}`;
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const resources = await loadResources();
  const english = locale === "en";
  const path = "/resources";
  const title = english ? "Technical resources" : "منابع فنی";
  return { title, description: english ? "Published technical documents for products." : "اسناد فنی منتشرشده محصولات.", robots: resources.length ? undefined : { index: false, follow: true }, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, url: absoluteUrl(localizedPath(locale, path)), locale: english ? "en_US" : "fa_IR", type: "website" } };
}

export default async function ResourcesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const resources = await loadResources();
  const english = locale === "en";
  const jsonLd = resources.length ? { "@context": "https://schema.org", "@type": "ItemList", name: english ? "Technical resources" : "منابع فنی", itemListElement: resources.map((resource, index) => ({ "@type": "ListItem", position: index + 1, name: resource.title, url: resource.file_url })) } : null;
  return <><main className="public-page site-container"><nav className="public-breadcrumb" aria-label="Breadcrumb"><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "Technical resources" : "منابع فنی"}</b></nav><header className="content-index-heading"><span>{english ? "Product documentation" : "مستندات محصولات"}</span><h1>{english ? "Technical resources" : "منابع فنی"}</h1></header>{resources.length ? <div className="resource-list">{resources.map((resource: ProductResource) => { const demo = resource.title.startsWith("[DEMO]") || resource.display_name.startsWith("[DEMO]"); const size = formatSize(resource.size, english); return <article className="resource-row" key={resource.id}><div className="resource-row-heading"><span className="resource-type">{documentTypeLabel(resource.type, english)}</span>{demo && <span className="content-demo-indicator">{english ? "Demo" : "نمونه"}</span>}<h2>{resource.title}</h2></div><p className="resource-product"><Link href={`/${locale}/product/${resource.product.slug}`}>{resource.product.name}</Link><br /><bdi dir="ltr">{resource.product.code}</bdi></p><dl className="resource-metadata">{resource.file_name && <div><dt>{english ? "File" : "فایل"}</dt><dd dir="ltr">{resource.file_name}</dd></div>}{resource.language && <div><dt>{english ? "Language" : "زبان"}</dt><dd>{resource.language}</dd></div>}{resource.revision && <div><dt>{english ? "Revision" : "ویرایش"}</dt><dd dir="ltr">{resource.revision}</dd></div>}{size && <div><dt>{english ? "Size" : "حجم"}</dt><dd dir="ltr">{size}</dd></div>}</dl><a className="btn-secondary" href={resource.file_url} download={resource.file_name || undefined} target="_blank" rel="noreferrer" aria-label={`${english ? "Download" : "دانلود"} ${resource.title}`}>{english ? "Download" : "دانلود"}</a></article>; })}</div> : <p className="home-section-empty">{english ? "No published technical resources are available." : "منبع فنی منتشرشده‌ای در دسترس نیست."}</p>}</main>{jsonLd && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />}</>;
}
