import Link from "next/link";
import { EditorialCard, FAQContextLinks, faqTypeLabel, localizedFAQ } from "../content/editorial";
import { ProductCard, type CatalogProduct } from "../catalog/product-card";
import type { SiteSearchBrand, SiteSearchCategory, SiteSearchProduct } from "../../lib/api/search";
import type { EditorialArticle, FAQEntry } from "../../types/api";

function productCard(product: SiteSearchProduct): CatalogProduct {
  return { id: product.id, name: product.name, slug: product.slug, code: product.code, unit: product.unit, available_quantity: null, category: product.category ? { name_fa: product.category.name_fa } : null, images: product.image ? [{ image: product.image, alt_text: product.name, alt_fa: product.name, is_primary: true }] : [], price: null };
}

export function SearchProductGroup({ products, locale, query }: { products: SiteSearchProduct[]; locale: string; query: string }) {
  if (!products.length) return null;
  return <section id="search-products" className="site-search-group" aria-labelledby="search-products-title"><header><h2 id="search-products-title">{locale === "en" ? "Products" : "محصولات"}</h2></header><div className="site-search-product-grid">{products.map((product) => <ProductCard key={product.id} product={productCard(product)} locale={locale} />)}</div><Link className="site-search-group-link" href={`/${locale}/shop?q=${encodeURIComponent(query)}`}>{locale === "en" ? "View all products" : "مشاهده همه محصولات"}<span aria-hidden="true">←</span></Link></section>;
}

export function SearchCategoryGroup({ categories, locale }: { categories: SiteSearchCategory[]; locale: string }) {
  if (!categories.length) return null;
  return <section id="search-categories" className="site-search-group" aria-labelledby="search-categories-title"><header><h2 id="search-categories-title">{locale === "en" ? "Categories" : "دسته‌بندی‌ها"}</h2></header><div className="site-search-links">{categories.map((category) => <Link key={category.id} href={`/${locale}/category/${category.slug}`}><strong>{locale === "en" && category.name_en ? category.name_en : category.name_fa}</strong><small>{category.product_count.toLocaleString(locale === "en" ? "en-US" : "fa-IR")} {locale === "en" ? "products" : "محصول"}</small></Link>)}</div></section>;
}

export function SearchBrandGroup({ brands, locale }: { brands: SiteSearchBrand[]; locale: string }) {
  if (!brands.length) return null;
  return <section id="search-brands" className="site-search-group" aria-labelledby="search-brands-title"><header><h2 id="search-brands-title">{locale === "en" ? "Brands" : "برندها"}</h2></header><div className="site-search-links site-search-brand-links">{brands.map((brand) => <Link key={brand.id} href={`/${locale}/brands/${brand.slug}`}>{brand.logo ? <img src={brand.logo} alt="" loading="lazy" /> : <span className="site-search-brand-mark" aria-hidden="true">◇</span>}<strong>{brand.name}</strong><small>{brand.product_count.toLocaleString(locale === "en" ? "en-US" : "fa-IR")} {locale === "en" ? "products" : "محصول"}</small></Link>)}</div></section>;
}

export function SearchEditorialGroup({ articles, locale }: { articles: EditorialArticle[]; locale: string }) {
  if (!articles.length) return null;
  return <section id="search-editorial" className="site-search-group" aria-labelledby="search-editorial-title"><header><h2 id="search-editorial-title">{locale === "en" ? "Knowledge & News" : "دانش و اخبار"}</h2></header><div className="site-search-editorial-grid">{articles.map((article) => <EditorialCard key={article.id} article={article} locale={locale} variant="compact" />)}</div></section>;
}

export function SearchFAQGroup({ faqs, locale }: { faqs: FAQEntry[]; locale: string }) {
  if (!faqs.length) return null;
  return <section id="search-faqs" className="site-search-group" aria-labelledby="search-faqs-title"><header><h2 id="search-faqs-title">{locale === "en" ? "Frequently Asked Questions" : "سوالات متداول"}</h2></header><div className="search-faq-results">{faqs.map((faq) => <article key={faq.id} className="search-faq-result"><small>{faqTypeLabel(faq, locale)}</small><h3><Link href={`/${locale}/faq#faq-${faq.slug}`}>{localizedFAQ(faq, locale, "question")}</Link></h3><p>{localizedFAQ(faq, locale, "answer").slice(0, 180)}{localizedFAQ(faq, locale, "answer").length > 180 ? "…" : ""}</p><FAQContextLinks faq={faq} locale={locale} /></article>)}</div></section>;
}

type SearchGroups = { products: SiteSearchProduct[]; categories: SiteSearchCategory[]; brands: SiteSearchBrand[]; articles: EditorialArticle[]; faqs: FAQEntry[] };
export function SearchGroupSummary({ groups, locale }: { groups: SearchGroups; locale: string }) {
  const labels = locale === "en" ? { products: "Products", categories: "Categories", brands: "Brands", articles: "Knowledge & News", faqs: "FAQs" } : { products: "محصولات", categories: "دسته‌بندی‌ها", brands: "برندها", articles: "دانش و اخبار", faqs: "سوالات متداول" };
  const entries = (Object.keys(labels) as Array<keyof SearchGroups>).filter((key) => groups[key].length > 0);
  if (entries.length < 2) return null;
  return <nav className="site-search-group-summary" aria-label={locale === "en" ? "Search result groups" : "گروه‌های نتایج جست‌وجو"}>{entries.map((key) => <a key={key} href={`#search-${key}`}><span>{labels[key]}</span><b>{groups[key].length.toLocaleString(locale === "en" ? "en-US" : "fa-IR")}</b></a>)}</nav>;
}

export function SearchEntryForm({ locale, query = "" }: { locale: string; query?: string }) {
  return <form className="site-search-form" action={`/${locale}/search`} method="get"><label htmlFor="site-search-page">{locale === "en" ? "Search products, categories, brands and knowledge" : "جست‌وجوی محصول، دسته‌بندی، برند و دانش"}</label><div><input id="site-search-page" name="q" defaultValue={query} maxLength={120} dir={locale === "en" ? "ltr" : undefined} /><button type="submit">{locale === "en" ? "Search" : "جست‌وجو"}</button></div></form>;
}
