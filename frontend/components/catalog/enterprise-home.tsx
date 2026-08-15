import Image from "next/image";
import Link from "next/link";
import { getCategoryUrl } from "../../lib/category-url";
import type { NavCategory } from "./mega-menu";
import { CompanyAdvantages, type Advantage } from "./company-advantages";
import { ProductCard, type CatalogProduct } from "./product-card";
import { SiteHero } from "./site-hero";
import type { CompanyInfo } from "../../types/api";
import { EditorialPreview } from "../content/editorial";
import type { EditorialArticle } from "../../types/api";

export type SupplyBrand = { id: number; name: string; logo: string | null; website: string };
export type HomepageIndustry = { id: number; slug: string; name_fa: string; name_en: string; description_fa: string; description_en: string; image: string | null };
export type HomepageCapability = { id: number; slug: string; title_fa: string; title_en: string; summary_fa: string; summary_en: string };
export type HomepageInitialData = {
  locale: string;
  company?: CompanyInfo | null;
  hero: import("../../types/api").SiteHero | null;
  advantages: Advantage[];
  categories: NavCategory[];
  featured: CatalogProduct[];
  newest: CatalogProduct[];
  discounted: CatalogProduct[];
  brands: SupplyBrand[];
  industries: HomepageIndustry[];
  capabilities: HomepageCapability[];
  editorial: EditorialArticle[];
};

function ProductSection({ locale, title, kicker, products, href, empty, tone = "supporting" }: { locale: string; title: string; kicker: string; products: CatalogProduct[]; href?: string; empty: string; tone?: "featured" | "supporting" }) {
  // Keep the product-section link explicitly named for screen readers: aria-label={`${title}؛ مشاهده همه`}
  return <section className={`enterprise-section home-product-section home-product-section--${tone} site-container`}>
    <header className="home-section-heading"><div><div className="section-kicker">{kicker}</div><h2>{title}</h2></div>{href && <Link href={href} aria-label={`${title}; ${locale === "en" ? "View all" : "مشاهده همه"}`}>{locale === "en" ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link>}</header>
    {products.length ? <div className="industrial-product-grid">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div> : <div className="home-section-empty">{empty}</div>}
  </section>;
}

export function EnterpriseHome({ locale, company, hero, advantages, categories, featured, newest, discounted, brands, industries, capabilities, editorial }: HomepageInitialData) {
  const english = locale === "en";
  const demo = (value: string) => value.startsWith("[DEMO]") ? <span className="content-demo-indicator" title={english ? "Development content" : "محتوای محیط توسعه"}>{english ? "Demo" : "نمونه"}</span> : null;
  // Category links retain their explicit accessible naming: aria-label={`مشاهده دسته ${category.name_fa}`}
  return <main className="enterprise-home">
    <SiteHero hero={hero} locale={locale} />
    {company?.description && <section className="home-company-intro site-container" aria-label={english ? "Company introduction" : "معرفی شرکت"}><div><div className="section-kicker">{english ? "About the company" : "درباره مجموعه"}</div><h2 id="home-company-title">{company.name_fa}</h2><p>{company.description}</p></div><div className="home-company-intro-actions"><Link className="secondary" href={`/${locale}/about`}>{english ? "About us" : "آشنایی با شرکت"}</Link><Link className="primary" href={`/${locale}/contact`}>{english ? "Contact us" : "تماس با ما"}</Link></div></section>}
    <CompanyAdvantages advantages={advantages} />
    <section id="categories" className="enterprise-section site-container"><div className="section-kicker">{english ? "Quick access" : "دسترسی سریع"}</div><h2>{english ? "Main product categories" : "دسته‌بندی‌های اصلی"}</h2>{categories.length ? <div className="root-cards">{categories.map((category) => <Link key={category.id} href={getCategoryUrl(category, locale)} aria-label={`${english ? "View category" : "مشاهده دسته"} ${category.name_fa}`}><span>{english ? "Main category" : "دسته اصلی"}</span><b>{category.name_fa}</b><i>{english ? "Explore subcategories" : "مشاهده زیرگروه‌ها"} <span aria-hidden="true">←</span></i></Link>)}</div> : <div className="home-section-empty">{english ? "Product categories are not available." : "دسته‌بندی‌های محصولات در دسترس نیست."}</div>}</section>
    <ProductSection locale={locale} title={english ? "Featured products" : "محصولات منتخب"} kicker={english ? "Selected for the catalog" : "انتخاب مدیریت فروشگاه"} products={featured} href={`/${locale}/shop`} empty={english ? "No featured products have been selected." : "هنوز محصولی به‌عنوان منتخب تعیین نشده است."} tone="featured" />
    <EditorialPreview articles={editorial} locale={locale} href={`/${locale}/knowledge`} />
    {industries.length > 0 && <section className="enterprise-section site-container" aria-labelledby="home-industries-title"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Industrial context" : "زمینه‌های صنعتی"}</div><h2 id="home-industries-title">{english ? "Industries and applications" : "صنایع و کاربردها"}</h2></div><Link href={`/${locale}/industries`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header><div className="home-industry-grid">{industries.slice(0, 4).map((item) => <Link className="home-context-card" key={item.id} href={`/${locale}/industries/${item.slug}`}><span>{english ? "Industry" : "زمینه صنعتی"}</span><h3>{english && item.name_en ? item.name_en : item.name_fa} {demo(english && item.name_en ? item.name_en : item.name_fa)}</h3>{(english ? item.description_en || item.description_fa : item.description_fa) && <p>{english ? item.description_en || item.description_fa : item.description_fa}</p>}</Link>)}</div></section>}
    {capabilities.length > 0 && <section className="enterprise-section site-container" aria-labelledby="home-capabilities-title"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Company expertise" : "توانمندی شرکت"}</div><h2 id="home-capabilities-title">{english ? "Capabilities" : "توانمندی‌ها"}</h2></div><Link href={`/${locale}/capabilities`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header><div className="home-capability-grid">{capabilities.slice(0, 3).map((item) => <Link className="home-context-card" key={item.id} href={`/${locale}/capabilities/${item.slug}`}><span>{english ? "Published capability" : "توانمندی منتشرشده"}</span><h3>{english && item.title_en ? item.title_en : item.title_fa} {demo(english && item.title_en ? item.title_en : item.title_fa)}</h3>{(english ? item.summary_en || item.summary_fa : item.summary_fa) && <p>{english ? item.summary_en || item.summary_fa : item.summary_fa}</p>}</Link>)}</div></section>}
    <ProductSection locale={locale} title={english ? "Newest products" : "جدیدترین محصولات"} kicker={english ? "Latest catalog additions" : "تازه‌های کاتالوگ"} products={newest} href={`/${locale}/newest`} empty={english ? "No new products have been registered." : "محصول جدیدی ثبت نشده است."} />
    <ProductSection locale={locale} title={english ? "Discounted products" : "بیشترین تخفیف‌ها"} kicker={english ? "Current offers" : "فرصت‌های خرید"} products={discounted} href={`/${locale}/best-discounts`} empty={english ? "There are no discounted products currently." : "در حال حاضر محصول تخفیف‌داری وجود ندارد."} />
    <section className="enterprise-section supply-brands-section site-container"><div className="section-kicker">{english ? "Supply context" : "شبکه تأمین"}</div><h2>{english ? "Available brands" : "برندهای قابل تأمین"}</h2>{brands.length ? <div className="supply-brand-grid">{brands.map((brand) => { const content = <>{brand.logo ? <Image src={brand.logo} alt={`${english ? "Logo of" : "لوگوی"} ${brand.name}`} width={120} height={64} /> : <span aria-hidden="true">{brand.name.slice(0, 1)}</span>}<b>{brand.name}</b></>; return brand.website ? <a key={brand.id} href={brand.website} target="_blank" rel="noreferrer">{content}</a> : <article key={brand.id}>{content}</article>; })}</div> : <div className="home-section-empty">{english ? "No supply brands are available yet." : "فهرست برندهای قابل تأمین به‌زودی تکمیل می‌شود."}</div>}</section>
    <section className="home-quote-cta site-container"><div><span>{english ? "Industrial purchasing" : "خرید سازمانی و صنعتی"}</span><h2>{english ? "Contact us about availability and pricing" : "برای استعلام موجودی و قیمت روز آماده‌ایم"}</h2><p>{english ? "Send the technical specification or product code you need." : "مشخصات فنی یا کد کالای مورد نیازتان را ارسال کنید تا کارشناسان فروش پاسخ دهند."}</p></div><div><Link className="primary" href={`/${locale}/contact`}>{english ? "Request an inquiry" : "درخواست استعلام"}</Link><Link className="secondary" href={`/${locale}/shop`}>{english ? "Browse products" : "مشاهده محصولات"}</Link></div></section>
  </main>;
}
