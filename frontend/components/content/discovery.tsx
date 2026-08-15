import Link from "next/link";
import type { DiscoveryResource, DiscoveryProduct, DiscoveryResult } from "../../lib/api/content";
import { EditorialCard, FAQList } from "./editorial";

function resourceLabel(type: string, locale: string) {
  const labels: Record<string, [string, string]> = { datasheet: ["دیتاشیت", "Datasheet"], manual: ["راهنما", "Manual"], cad: ["فایل CAD", "CAD"], certificate: ["گواهی", "Certificate"], catalogue: ["کاتالوگ", "Catalogue"], other: ["سند فنی", "Other"] };
  return labels[type]?.[locale === "en" ? 1 : 0] || type;
}

export function DiscoveryResources({ resources, locale }: { resources: DiscoveryResource[]; locale: string }) {
  if (!resources.length) return null;
  return <section className="discovery-section" aria-labelledby="discovery-resources-title"><header><span>{locale === "en" ? "Technical library" : "کتابخانه فنی"}</span><h2 id="discovery-resources-title">{locale === "en" ? "Related Technical Resources" : "منابع فنی مرتبط"}</h2></header><ul className="discovery-resource-list">{resources.map((resource) => <li key={resource.id}><div><small>{resourceLabel(resource.type, locale)}{resource.revision ? " · Rev. " + resource.revision : ""}{resource.language ? " · " + resource.language : ""}</small><strong>{resource.title || resource.display_name || resource.file_name}</strong><span dir="ltr">{resource.file_name}</span></div><a href={resource.file_url} target="_blank" rel="noreferrer" download={resource.file_name || undefined}>{locale === "en" ? "Download" : "دانلود"}</a></li>)}</ul></section>;
}

export function DiscoveryProducts({ products, locale, title }: { products: DiscoveryProduct[]; locale: string; title?: string }) {
  if (!products.length) return null;
  return <section className="discovery-section" aria-labelledby="discovery-products-title"><header><span>{locale === "en" ? "Catalog context" : "زمینه کاتالوگ"}</span><h2 id="discovery-products-title">{title || (locale === "en" ? "Related Products" : "محصولات مرتبط")}</h2></header><div className="discovery-product-links">{products.map((product) => <Link key={product.id} href={`/${locale}/product/${product.slug}`}><span dir="ltr">{product.code}</span><strong>{product.name_fa}</strong></Link>)}</div></section>;
}

export function ArticleDiscovery({ discovery, locale }: { discovery: DiscoveryResult; locale: string }) {
  return <>{discovery.products.length > 0 && <DiscoveryProducts products={discovery.products} locale={locale} />}{discovery.resources.length > 0 && <DiscoveryResources resources={discovery.resources} locale={locale} />}{discovery.faqs.length > 0 && <FAQList faqs={discovery.faqs} locale={locale} compact title={locale === "en" ? "Related FAQs" : "سوالات مرتبط"} />}{discovery.articles.length > 0 && <section className="discovery-section" aria-labelledby="discovery-articles-title"><header><span>{locale === "en" ? "Continue reading" : "ادامه مطالعه"}</span><h2 id="discovery-articles-title">{locale === "en" ? "Related Articles" : "مطالب مرتبط"}</h2></header><div className="editorial-card-grid">{discovery.articles.map((article) => <EditorialCard key={article.id} article={article} locale={locale} variant="compact" />)}</div></section>}</>;
}
