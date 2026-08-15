import type { Metadata } from "next";
import Link from "next/link";
import { getCapabilitiesServer } from "../../../lib/api/content";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../lib/locale-url";

type Capability = { id: number; slug: string; title_fa: string; title_en: string; summary_fa: string; summary_en: string; icon: string; image: string | null; cta_label_fa: string; cta_label_en: string; cta_url: string; categories: { id: number; name_fa: string; name_en: string; slug: string }[]; products: { id: number; name: string; code: string; slug: string }[] };

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params; const path = "/capabilities"; const title = locale === "en" ? "Capabilities" : "توانمندی‌ها";
  return { title, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, url: absoluteUrl(localizedPath(locale, path)), locale: locale === "en" ? "en_US" : "fa_IR", type: "website" } };
}

export default async function CapabilitiesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params; const capabilities = await getCapabilitiesServer<Capability[]>().catch(() => []); const english = locale === "en";
  const jsonLd = capabilities.length ? { "@context": "https://schema.org", "@type": "ItemList", name: english ? "Capabilities" : "توانمندی‌ها", itemListElement: capabilities.map((item, index) => ({ "@type": "ListItem", position: index + 1, name: english && item.title_en ? item.title_en : item.title_fa, url: absoluteUrl(localizedPath(locale, `/capabilities/${item.slug}`)) })) } : null;
  return <><main className="public-page site-container"><nav className="public-breadcrumb" aria-label="Breadcrumb"><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><b>{english ? "Capabilities" : "توانمندی‌ها"}</b></nav><header className="content-index-heading"><span>{english ? "Company expertise" : "توانمندی شرکت"}</span><h1>{english ? "Capabilities" : "توانمندی‌ها"}</h1></header>{capabilities.length > 0 ? <div className="content-card-grid content-card-grid--capabilities">{capabilities.map((item) => { const title = english && item.title_en ? item.title_en : item.title_fa; const demo = title.startsWith("[DEMO]"); return <article className="content-card" key={item.id}><span aria-hidden="true">{item.icon || ""}</span><h2><Link href={`/${locale}/capabilities/${item.slug}`}>{title}</Link>{demo && <span className="content-demo-indicator">{english ? "Demo" : "نمونه"}</span>}</h2>{(english ? item.summary_en || item.summary_fa : item.summary_fa) && <p>{english ? item.summary_en || item.summary_fa : item.summary_fa}</p>}</article>; })}</div> : <p className="home-section-empty">{english ? "No published capabilities are available." : "توانمندی منتشرشده‌ای در دسترس نیست."}</p>}</main>{jsonLd && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />}</>;
}
