import Image from "next/image";
import Link from "next/link";
import { getCategoryUrl } from "../../lib/category-url";
import type { NavCategory } from "../../lib/nav-category";
import { CompanyAdvantages, type Advantage } from "./company-advantages";
import { ProductCard, type CatalogProduct } from "./product-card";
import { SiteHero } from "./site-hero";
import type { CompanyInfo, SiteHeroCategorySpotlight, SiteHeroPromotion } from "../../types/api";
import { EditorialPreview } from "../content/editorial";
import type { EditorialArticle } from "../../types/api";
import { formatNumber } from "../../lib/product/formatters";

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
  bestSelling: CatalogProduct[];
  newest: CatalogProduct[];
  discounted: CatalogProduct[];
  lowStock: CatalogProduct[];
  brands: SupplyBrand[];
  industries: HomepageIndustry[];
  capabilities: HomepageCapability[];
  editorial: EditorialArticle[];
};

const categoryArtwork = ["fancoil", "compressor-green", "axial", "exchanger", "expansion", "pcb", "copper", "pump", "bearing", "gauge"] as const;

function ProductSection({ locale, title, kicker, products, href, empty, tone = "supporting", skin = "default", promotion }: { locale: string; title: string; kicker: string; products: CatalogProduct[]; href?: string; empty: string; tone?: "featured" | "supporting"; skin?: "default" | "best" | "newest" | "discount" | "low-stock"; promotion?: SiteHeroPromotion | null }) {
  // Keep the product-section link explicitly named for screen readers: aria-label={`${title}؛ مشاهده همه`}
  const english = locale === "en";
  return <section className={`enterprise-section home-product-section home-product-section--${tone} home-product-section--${skin} site-container`}>
    <header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{kicker}</div><h2>{title}</h2></div>{href && <Link className="mehrasl-text-link" href={href} aria-label={`${title}; ${locale === "en" ? "View all" : "مشاهده همه"}`}>{locale === "en" ? "View all" : "مشاهده همه"} <span aria-hidden="true" className="rtl:rotate-180 inline-block">←</span></Link>}</header>
    {products.length ? tone === "featured" && promotion ? <div className="mehrasl-special-layout"><aside className="mehrasl-special-promo">{promotion.image && <Image className="mehrasl-special-promo-image" src={promotion.image} alt={promotion.title} width={220} height={160} />}<span>{english ? "Special offer" : "پیشنهاد ویژه"}</span><strong><b>{formatNumber(promotion.discount_percentage)}</b><small>{english ? "% off" : "٪ تا"}</small></strong><h3>{promotion.title}</h3>{promotion.description && <p>{promotion.description}</p>}{promotion.button && <Link href={promotion.button.link}>{promotion.button.text} <span aria-hidden="true">←</span></Link>}</aside><div className="industrial-product-grid">{products.slice(0, 3).map((product) => <ProductCard key={product.id} product={product} locale={locale} />)}</div></div> : <div className="industrial-product-grid">{products.slice(0, 4).map((product) => <ProductCard key={product.id} product={product} locale={locale} />)}</div> : <div className="home-section-empty">{empty}</div>}
  </section>;
}

function CompanyPromotionStrip({ locale, promotions }: { locale: string; promotions: SiteHeroPromotion[] }) {
  const english = locale === "en";
  const typeLabel = (type: SiteHeroPromotion["promotion_type"]) => english ? (type === "product" ? "Product offer" : type === "brand" ? "Brand spotlight" : "MehrAsl offer") : (type === "product" ? "پیشنهاد محصول" : type === "brand" ? "ویژه برندها" : "پیشنهاد مهراصل");
  if (!promotions.length) return null;
  return <section className="company-promotion-strip site-container" aria-label={english ? "Company promotions" : "تبلیغات مهراصل"}>
    {promotions.map((promotion) => {
      const content = <>{promotion.image && <Image src={promotion.image} alt={promotion.title} width={220} height={150} />}<div><span>{typeLabel(promotion.promotion_type)}</span><h2>{promotion.title}</h2>{promotion.description && <p>{promotion.description}</p>}{promotion.button && <b>{promotion.button.text} <i aria-hidden="true">←</i></b>}</div></>;
      return promotion.button ? <Link className={`company-promotion-card company-promotion-card--${promotion.promotion_type}`} href={promotion.button.link} key={promotion.id}>{content}</Link> : <article className={`company-promotion-card company-promotion-card--${promotion.promotion_type}`} key={promotion.id}>{content}</article>;
    })}
  </section>;
}

function CategorySpotlightStrip({ locale, item }: { locale: string; item?: SiteHeroCategorySpotlight }) {
  const english = locale === "en";
  if (!item) return null;
  return <section className="category-spotlight-strip site-container" aria-label={english ? "Featured categories" : "دسته‌بندی‌های مهم"}>
    <Link className={`category-spotlight-card category-spotlight-card--${item.placement === "between_newest_discounts" ? "warm" : "fresh"}`} href={`/${locale}/category/${encodeURIComponent(item.category_slug)}`}>
      {item.image && <Image src={item.image} alt={item.title} width={260} height={180} />}
      <div><span>{english ? "Featured category" : "دسته‌بندی منتخب"}</span><h2>{item.title}</h2>{item.description && <p>{item.description}</p>}<b>{item.button_text} <i aria-hidden="true">←</i></b></div>
    </Link>
  </section>;
}

export function EnterpriseHome({ locale, company, hero, advantages, categories, featured, bestSelling, newest, discounted, lowStock, brands, industries, capabilities, editorial }: HomepageInitialData) {
  const english = locale === "en";
  const spotlightAt = (placement: SiteHeroCategorySpotlight["placement"]) => hero?.category_spotlights?.find((item) => item.placement === placement);
  const demo = (value: string) => value.startsWith("[DEMO]") ? <span className="content-demo-indicator" title={english ? "Development content" : "محتوای محیط توسعه"}>{english ? "Demo" : "نمونه"}</span> : null;
  // Category links retain their explicit accessible naming: aria-label={`مشاهده دسته ${category.name_fa}`}
  return <main className="enterprise-home mehrasl-storefront">
    <SiteHero hero={hero} locale={locale} />
    <CompanyAdvantages advantages={advantages} />
    <section className="mehrasl-shopping-path site-container" aria-label={english ? "Shopping path" : "مسیر خرید"}>
      {[english ? ["01", "Precise selection", "Search by product name and code"] : ["۰۱", "انتخاب دقیق‌تر", "جست‌وجو با نام، مدل و کد"], english ? ["02", "Clear availability", "See stock status before ordering"] : ["۰۲", "موجودی روشن", "وضعیت کالا پیش از سفارش"], english ? ["03", "Technical support", "Help choosing the right product"] : ["۰۳", "پشتیبانی فنی", "برای انتخاب محصول و قطعه"], english ? ["04", "Trackable delivery", "Follow every order step"] : ["۰۴", "تحویل قابل پیگیری", "از ثبت سفارش تا دریافت کالا"]].map(([number, title, text]) => <article key={number}><span>{number}</span><div><h2>{title}</h2><p>{text}</p></div></article>)}
    </section>
    {company?.description && <section className="home-company-intro site-container mehrasl-company-intro" aria-label={english ? "Company introduction" : "معرفی شرکت"}><div><div className="section-kicker">{english ? "About the company" : "درباره مجموعه"}</div><h2 id="home-company-title">{company.name_fa}</h2><p>{company.description}</p></div><div className="home-company-intro-actions"><Link className="secondary" href={`/${locale}/about`}>{english ? "About us" : "آشنایی با شرکت"}</Link><Link className="primary" href={`/${locale}/contact`}>{english ? "Contact us" : "تماس با ما"}</Link></div></section>}
    <section id="categories" className="enterprise-section site-container mehrasl-categories" aria-labelledby="home-categories-title"><header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{english ? "Your shopping path" : "مسیر خرید شما"}</div><h2 id="home-categories-title">{english ? "Where would you like to start?" : "از کدام دسته شروع می‌کنید؟"}</h2></div><Link className="mehrasl-text-link" href={`/${locale}/categories`}>{english ? "All categories" : "همه دسته‌ها"} <span aria-hidden="true">←</span></Link></header>{categories.length ? <div className="root-cards">{categories.slice(0, 10).map((category, index) => <Link key={category.id} href={getCategoryUrl(category, locale)} aria-label={`${english ? "View category" : "مشاهده دسته"} ${category.name_fa}`}><span className="mehrasl-category-number">{String(index + 1).padStart(2, "0")}</span><span className="mehrasl-category-art" aria-hidden="true"><Image src={`/images/category-art/${categoryArtwork[index % categoryArtwork.length]}.svg`} alt="" width={96} height={76} /></span><b>{category.name_fa}</b><i>{english ? "Explore" : "مشاهده محصولات"} <span aria-hidden="true">←</span></i></Link>)}</div> : <div className="home-section-empty">{english ? "Product categories are not available." : "دسته‌بندی‌های محصولات در دسترس نیست."}</div>}</section>
    <ProductSection locale={locale} title={english ? "Featured products" : "محصولات منتخب"} kicker={english ? "Selected for the catalog" : "انتخاب مدیریت فروشگاه"} products={featured} href={`/${locale}/shop`} empty={english ? "No featured products have been selected." : "هنوز محصولی به‌عنوان منتخب تعیین نشده است."} tone="featured" promotion={hero?.featured_promotion} />
    <CategorySpotlightStrip locale={locale} item={spotlightAt("after_featured")} />
    <ProductSection locale={locale} title={english ? "Best sellers" : "پرفروش‌ترین‌ها"} kicker={english ? "Most ordered products" : "محبوب‌ترین انتخاب مشتریان"} products={bestSelling} href={`/${locale}/shop?best_sellers=true`} empty={english ? "Best sellers will appear after the first confirmed orders." : "پرفروش‌ترین‌ها پس از ثبت نخستین سفارش‌های تأییدشده نمایش داده می‌شوند."} skin="best" />
    <CategorySpotlightStrip locale={locale} item={spotlightAt("after_best_sellers")} />
    <CompanyPromotionStrip locale={locale} promotions={(hero?.home_promotions || []).filter((promotion) => promotion.placement === "home_middle")} />
    <section className="mehrasl-split-promos site-container" aria-label={english ? "MehrAsl services" : "خدمات مهراصل"}>
      <Link href={`/${locale}/about`}><span>{english ? "About MehrAsl" : "معرفی مجموعه مهراصل"}</span><h2>{english ? "A dependable partner for specialist industrial purchasing." : `${company?.name_fa || "مهراصل"}؛ همراه مطمئن خریدهای تخصصی شما.`}</h2><b>{english ? "Get to know us" : "آشنایی با مجموعه"} ←</b></Link>
      <Link href={`/${locale}/rfq`}><span>{english ? "Project purchasing" : "خرید پروژه‌ای و سازمانی"}</span><h2>{english ? "Get technical guidance and a tailored quotation for your project." : "مشاوره فنی و پیش‌فاکتور متناسب با پروژه‌تان را دریافت کنید."}</h2><b>{english ? "Request a quote" : "درخواست پیش‌فاکتور"} ←</b></Link>
    </section>
    {industries.length > 0 && <section className="enterprise-section site-container" aria-labelledby="home-industries-title"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Industrial context" : "زمینه‌های صنعتی"}</div><h2 id="home-industries-title">{english ? "Industries and applications" : "صنایع و کاربردها"}</h2></div><Link href={`/${locale}/industries`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header><div className="home-industry-grid">{industries.slice(0, 3).map((item) => <Link className="home-context-card" key={item.id} href={`/${locale}/industries/${item.slug}`}><span>{english ? "Industry" : "زمینه صنعتی"}</span><h3>{english && item.name_en ? item.name_en : item.name_fa} {demo(english && item.name_en ? item.name_en : item.name_fa)}</h3>{(english ? item.description_en || item.description_fa : item.description_fa) && <p>{english ? item.description_en || item.description_fa : item.description_fa}</p>}</Link>)}</div></section>}
    {capabilities.length > 0 && <section className="enterprise-section site-container" aria-labelledby="home-capabilities-title"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Company expertise" : "توانمندی شرکت"}</div><h2 id="home-capabilities-title">{english ? "Capabilities" : "توانمندی‌ها"}</h2></div><Link href={`/${locale}/capabilities`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header><div className="home-capability-grid">{capabilities.slice(0, 3).map((item) => <Link className="home-context-card" key={item.id} href={`/${locale}/capabilities/${item.slug}`}><span>{english ? "Published capability" : "توانمندی منتشرشده"}</span><h3>{english && item.title_en ? item.title_en : item.title_fa} {demo(english && item.title_en ? item.title_en : item.title_fa)}</h3>{(english ? item.summary_en || item.summary_fa : item.summary_fa) && <p>{english ? item.summary_en || item.summary_fa : item.summary_fa}</p>}</Link>)}</div></section>}
    <ProductSection locale={locale} title={english ? "Newest products" : "جدیدترین محصولات"} kicker={english ? "Latest catalog additions" : "تازه‌های کاتالوگ"} products={newest} href={`/${locale}/newest`} empty={english ? "No new products have been registered." : "محصول جدیدی ثبت نشده است."} skin="newest" />
    <CategorySpotlightStrip locale={locale} item={spotlightAt("between_newest_discounts")} />
    <ProductSection locale={locale} title={english ? "Discounted products" : "بیشترین تخفیف‌ها"} kicker={english ? "Current offers" : "فرصت‌های خرید"} products={discounted} href={`/${locale}/best-discounts`} empty={english ? "There are no discounted products currently." : "در حال حاضر محصول تخفیف‌داری وجود ندارد."} skin="discount" />
    <CategorySpotlightStrip locale={locale} item={spotlightAt("after_discounts")} />
    <ProductSection locale={locale} title={english ? "Running low" : "محصولات در حال اتمام"} kicker={english ? "Limited remaining inventory" : "موجودی محدود؛ پیش از اتمام تهیه کنید"} products={lowStock} href={`/${locale}/shop?low_stock=true`} empty={english ? "No products currently have limited available stock." : "در حال حاضر محصولی با موجودی محدود ثبت نشده است."} skin="low-stock" />
    <CategorySpotlightStrip locale={locale} item={spotlightAt("after_low_stock")} />
    <section className="enterprise-section supply-brands-section site-container"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Supply context" : "شبکه تأمین"}</div><h2>{english ? "Available brands" : "برندهای قابل تأمین"}</h2></div><Link href={`/${locale}/brands`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header>{brands.length ? <div className="supply-brand-grid">{brands.slice(0, 6).map((brand) => { const content = <>{brand.logo ? <Image src={brand.logo} alt={`${english ? "Logo of" : "لوگوی"} ${brand.name}`} width={120} height={64} /> : <span aria-hidden="true">{brand.name.slice(0, 1)}</span>}<b>{brand.name}</b></>; return brand.website ? <a key={brand.id} href={brand.website} target="_blank" rel="noreferrer">{content}</a> : <article key={brand.id}>{content}</article>; })}</div> : <div className="home-section-empty">{english ? "No supply brands are available yet." : "فهرست برندهای قابل تأمین به‌زودی تکمیل می‌شود."}</div>}</section>
    <CompanyPromotionStrip locale={locale} promotions={(hero?.home_promotions || []).filter((promotion) => promotion.placement === "home_bottom")} />
    <EditorialPreview articles={editorial} locale={locale} href={`/${locale}/knowledge`} />
    <section className="home-quote-cta site-container"><div><span>{english ? "Industrial purchasing" : "ویژه پیمانکاران، شرکت‌ها و همکاران"}</span><h2>{english ? "Contact us about availability and pricing" : "برای خرید پروژه‌ای، مسیر جدا داریم."}</h2><p>{english ? "Send the technical specification or product code you need." : "فهرست نیازتان را آماده کنید؛ درخواست پیش‌فاکتور و بررسی فنی از همین‌جا شروع می‌شود."}</p></div><div><Link className="primary" href={`/${locale}/rfq`}>{english ? "Request an inquiry" : "درخواست پیش‌فاکتور"}</Link><Link className="secondary" href={`/${locale}/shop`}>{english ? "Browse products" : "مشاهده محصولات"}</Link></div></section>
  </main>;
}
