import { FiSearch, FiCheckCircle, FiHeadphones, FiTruck } from "react-icons/fi";
import Image from "next/image";
import Link from "next/link";
import { getCategoryUrl } from "../../lib/category-url";
import type { NavCategory } from "../../lib/nav-category";
import { CompanyAdvantages, type Advantage } from "./company-advantages";
import { ProductCard, type CatalogProduct } from "./product-card";
import { SiteHero } from "./site-hero";
import type { CompanyInfo, SiteHeroCategorySpotlight } from "../../types/api";
import { EditorialPreview } from "../content/editorial";
import { TrustSections, type CompanyCertification, type CompanyHonor } from "./trust-sections";
import type { EditorialArticle } from "../../types/api";

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
  industries: HomepageIndustry[];
  capabilities: HomepageCapability[];
  editorial: EditorialArticle[];
  certifications: CompanyCertification[];
  honors: CompanyHonor[];
};

const categoryArtwork = ["fancoil", "compressor-green", "axial", "exchanger", "expansion", "pcb", "copper", "pump", "bearing", "gauge"] as const;

function ProductSection({ locale, title, kicker, products, href, empty, tone = "supporting", skin = "default" }: { locale: string; title: string; kicker: string; products: CatalogProduct[]; href?: string; empty?: string; tone?: "featured" | "supporting"; skin?: "default" | "best" | "newest" | "discount" | "low-stock" }) {
  // Keep the product-section link explicitly named for screen readers: aria-label={`${title}؛ مشاهده همه`}
  const english = locale === "en";
  // Do not show a merchandising heading with an empty placeholder on the public home page.
  return <section className={`enterprise-section home-product-section home-product-section--${tone} home-product-section--${skin} site-container`}>
    <header className="home-section-heading mehrasl-section-heading"><div><div className="section-kicker">{kicker}</div><h2>{title}</h2></div>{href && <Link className="mehrasl-text-link" href={href} aria-label={`${title}; ${locale === "en" ? "View all" : "مشاهده همه"}`}>{locale === "en" ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link>}</header>
    {products.length ? <div className="industrial-product-grid home-product-grid">{products.slice(0, 4).map((product) => <ProductCard key={product.id} product={product} locale={locale} />)}</div> : <div className="home-section-empty home-section-empty--action"><p>{empty}</p>{href && <Link href={href}>{english ? "Browse all products" : "مشاهده همه محصولات"} <span aria-hidden="true">←</span></Link>}</div>}
  </section>;
}

function CategorySpotlightStrip({ locale, items }: { locale: string; items: SiteHeroCategorySpotlight[] }) {
  const english = locale === "en";
  if (!items.length) return null;
  const ordered = [...items].sort((a, b) => (a.side === b.side ? a.order - b.order : a.side === "right" ? -1 : 1));
  return <section className="category-spotlight-strip site-container" aria-label={english ? "Featured categories" : "دسته‌بندی‌های مهم"}>
    {ordered.map((item) => <Link key={item.id} className={`category-spotlight-card category-spotlight-card--${item.placement === "between_newest_discounts" ? "warm" : "fresh"} ${item.side === "left" ? "category-spotlight-card--left" : "category-spotlight-card--right"}${item.image ? " category-spotlight-card--image" : ""}${item.category_slug === "type-2-group-13" ? " category-spotlight-card--fan-coil" : ""}${item.category_slug === "type-2" && item.placement === "after_discounts" ? " category-spotlight-card--manufactured" : ""}`} href={`/${locale}/category/${encodeURIComponent(item.category_slug)}`}>
      {item.image && <Image src={item.image} alt="" fill sizes="(max-width: 1050px) 100vw, 50vw" className="category-spotlight-background" />}
      <div>{!item.image && <span>{english ? "Featured category" : "دسته‌بندی منتخب"}</span>}<h2>{item.title}</h2>{item.description && <p>{item.description}</p>}<b>{item.button_text} <i aria-hidden="true">←</i></b></div>
    </Link>)}
  </section>;
}

export function EnterpriseHome({ locale, company, hero, advantages, categories, featured, bestSelling, newest, discounted, lowStock, industries, capabilities, editorial, certifications, honors }: HomepageInitialData) {
  const english = locale === "en";
  const spotlightsAt = (placement: SiteHeroCategorySpotlight["placement"]) => (hero?.category_spotlights || []).filter((item) => item.placement === placement);
  const demo = (value: string) => value.startsWith("[DEMO]") ? <span className="content-demo-indicator" title={english ? "Development content" : "محتوای محیط توسعه"}>{english ? "Demo" : "نمونه"}</span> : null;
  // Category links retain their explicit accessible naming: aria-label={`مشاهده دسته ${category.name_fa}`}
  return <main className="enterprise-home mehrasl-storefront">
    <SiteHero hero={hero} locale={locale} />
    <CompanyAdvantages advantages={advantages} />
    <section className="mehrasl-shopping-path site-container" aria-label={english ? "Shopping path" : "مسیر خرید"}>
      {[
        { id: "select", icon: <FiSearch size={18} aria-hidden="true" />, title: english ? "Precise selection" : "انتخاب دقیق‌تر", text: english ? "Search by product name and code" : "جست‌وجو با نام، مدل و کد" },
        { id: "stock", icon: <FiCheckCircle size={18} aria-hidden="true" />, title: english ? "Clear availability" : "موجودی روشن", text: english ? "See stock status before ordering" : "وضعیت کالا پیش از سفارش" },
        { id: "support", icon: <FiHeadphones size={18} aria-hidden="true" />, title: english ? "Technical support" : "پشتیبانی فنی", text: english ? "Help choosing the right product" : "برای انتخاب محصول و قطعه" },
        { id: "delivery", icon: <FiTruck size={18} aria-hidden="true" />, title: english ? "Trackable delivery" : "تحویل قابل پیگیری", text: english ? "Follow every order step" : "از ثبت سفارش تا دریافت کالا" },
      ].map((step) => (
        <article key={step.id}>
          <span>{step.icon}</span>
          <div>
            <h2>{step.title}</h2>
            <p>{step.text}</p>
          </div>
        </article>
      ))}
    </section>
    {company?.description && <section className="home-company-intro site-container mehrasl-company-intro" aria-label={english ? "Company introduction" : "معرفی شرکت"}><div><div className="section-kicker">{english ? "About the company" : "درباره مجموعه"}</div><h2 id="home-company-title">{company.name_fa}</h2><p>{company.description}</p></div><div className="home-company-intro-actions"><Link className="secondary" href={`/${locale}/about`}>{english ? "About us" : "آشنایی با شرکت"}</Link><Link className="primary" href={`/${locale}/contact`}>{english ? "Contact us" : "تماس با ما"}</Link></div></section>}
    <section id="categories" className="enterprise-section site-container mehrasl-categories" aria-labelledby="home-categories-title"><header className="home-section-heading mehrasl-section-heading"><div><h2 id="home-categories-title">{english ? "Where would you like to start?" : "از کدام دسته شروع می‌کنید؟"}</h2></div><Link className="mehrasl-text-link" href={`/${locale}/categories`}>{english ? "All categories" : "همه دسته‌ها"} <span aria-hidden="true">←</span></Link></header>{categories.length ? <div className="root-cards">{categories.slice(0, 10).map((category, index) => <Link key={category.id} href={getCategoryUrl(category, locale)} aria-label={`${english ? "View category" : "مشاهده دسته"} ${category.name_fa}`}><span className={`mehrasl-category-art${category.image ? " mehrasl-category-art--custom" : ""}`} aria-hidden="true">{category.image ? <Image src={category.image} alt="" fill sizes="(max-width: 520px) 66px, 82px" /> : <Image src={`/images/category-art/${categoryArtwork[index % categoryArtwork.length]}.svg`} alt="" width={96} height={76} />}</span><b>{category.name_fa}</b><i>{english ? "Explore" : "مشاهده محصولات"} <span aria-hidden="true">←</span></i></Link>)}</div> : <div className="home-section-empty">{english ? "Product categories are not available." : "دسته‌بندی‌های محصولات در دسترس نیست."}</div>}</section>
    <ProductSection locale={locale} title={english ? "Featured products" : "محصولات منتخب"} kicker={english ? "Selected for the catalog" : "انتخاب مدیریت فروشگاه"} products={featured} href={`/${locale}/shop?catalog=featured&featured=1`} empty={english ? "No featured products have been selected yet." : "هنوز محصولی به‌عنوان منتخب تعیین نشده است."} tone="featured" />
    <CategorySpotlightStrip locale={locale} items={spotlightsAt("after_featured")} />
    <ProductSection locale={locale} title={english ? "Best sellers" : "پرفروش‌ترین‌ها"} kicker={english ? "Most ordered products" : "محبوب‌ترین انتخاب مشتریان"} products={bestSelling} href={`/${locale}/shop?best_sellers=true`} empty={english ? "Best sellers will appear after the first confirmed orders." : "پرفروش‌ترین‌ها پس از ثبت نخستین سفارش‌های تأییدشده نمایش داده می‌شوند."} skin="best" />
    <CategorySpotlightStrip locale={locale} items={spotlightsAt("after_best_sellers")} />
    <section className="ma-promo-grid mehrasl-split-promos site-container" aria-label={english ? "MehrAsl services" : "خدمات مهراصل"}>
      {/* کارت راست: معرفی مجموعه مهراصل */}
      <Link href={`/${locale}/about`} className="ma-promo-card ma-card-light" aria-label={english ? "About MehrAsl" : "معرفی مجموعه مهراصل"}>
        <div className="ma-card-content">
          <div className="ma-card-badge">
            <span className="ma-badge-dot" aria-hidden="true" />
            <span>{english ? "About MehrAsl" : "معرفی مجموعه مهراصل"}</span>
          </div>
          <h3 className="ma-card-title">
            {english ? "A dependable partner for specialist industrial purchasing." : `${company?.name_fa || "شرکت تولیدی مهر اصل"}؛ همراه مطمئن خریدهای تخصصی شما.`}
          </h3>
          <div className="ma-card-cta">
            <span>{english ? "Get to know us" : "آشنایی با مجموعه"}</span>
            <span className="ma-cta-arrow" aria-hidden="true">←</span>
          </div>
        </div>
        <div className="ma-card-image-wrap" aria-hidden="true">
          <Image
            src="/images/promo-about-factory-v3.png"
            alt=""
            width={380}
            height={360}
            className="ma-card-img"
          />
        </div>
      </Link>

      {/* کارت چپ: خرید پروژه‌ای و سازمانی */}
      <Link href={`/${locale}/rfq`} className="ma-promo-card ma-card-dark" aria-label={english ? "Project purchasing" : "خرید پروژه‌ای و سازمانی"}>
        <div className="ma-card-content">
          <div className="ma-card-badge">
            <span className="ma-badge-dot" aria-hidden="true" />
            <span>{english ? "Project purchasing" : "خرید پروژه‌ای و سازمانی"}</span>
          </div>
          <h3 className="ma-card-title">
            {english ? "Get technical guidance and a tailored quotation for your project." : "مشاوره فنی و استعلام قیمت متناسب با پروژه‌تان را دریافت کنید."}
          </h3>
          <div className="ma-card-cta">
            <span>{english ? "Request a quote" : "استعلام قیمت"}</span>
            <span className="ma-cta-arrow" aria-hidden="true">←</span>
          </div>
        </div>
        <div className="ma-card-image-wrap" aria-hidden="true">
          <Image
            src="/images/promo-rfq-engineering-v3.png"
            alt=""
            width={380}
            height={360}
            className="ma-card-img"
          />
        </div>
      </Link>
    </section>
    <TrustSections locale={locale} />
    {capabilities.length > 0 && <section className="enterprise-section site-container" aria-labelledby="home-capabilities-title"><header className="home-section-heading"><div><div className="section-kicker">{english ? "Company expertise" : "توانمندی شرکت"}</div><h2 id="home-capabilities-title">{english ? "Capabilities" : "توانمندی‌ها"}</h2></div><Link href={`/${locale}/capabilities`}>{english ? "View all" : "مشاهده همه"} <span aria-hidden="true">←</span></Link></header><div className="home-capability-grid">{capabilities.slice(0, 3).map((item) => <Link className="home-context-card" key={item.id} href={`/${locale}/capabilities/${item.slug}`}><span>{english ? "Published capability" : "توانمندی منتشرشده"}</span><h3>{english && item.title_en ? item.title_en : item.title_fa} {demo(english && item.title_en ? item.title_en : item.title_fa)}</h3>{(english ? item.summary_en || item.summary_fa : item.summary_fa) && <p>{english ? item.summary_en || item.summary_fa : item.summary_fa}</p>}</Link>)}</div></section>}
    <ProductSection locale={locale} title={english ? "Newest products" : "جدیدترین محصولات"} kicker={english ? "Latest catalog additions" : "تازه‌های کاتالوگ"} products={newest} href={`/${locale}/newest`} empty={english ? "No new products have been registered yet." : "محصول جدیدی ثبت نشده است."} skin="newest" />
    <CategorySpotlightStrip locale={locale} items={spotlightsAt("between_newest_discounts")} />
    <ProductSection locale={locale} title={english ? "Discounted products" : "بیشترین تخفیف‌ها"} kicker={english ? "Current offers" : "فرصت‌های خرید"} products={discounted} href={`/${locale}/best-discounts`} empty={english ? "There are no active discounts right now. Browse the catalog or check back soon." : "فعلاً تخفیف فعالی ثبت نشده است؛ می‌توانید همه محصولات را ببینید یا بعداً دوباره سر بزنید."} skin="discount" />
    <CategorySpotlightStrip locale={locale} items={spotlightsAt("after_discounts")} />
    <ProductSection locale={locale} title={english ? "Running low" : "محصولات در حال اتمام"} kicker={english ? "Limited remaining inventory" : "موجودی محدود؛ پیش از اتمام تهیه کنید"} products={lowStock} href={`/${locale}/shop?low_stock=true`} empty={english ? "No products currently have limited available stock." : "در حال حاضر محصولی با موجودی محدود ثبت نشده است."} skin="low-stock" />
    <CategorySpotlightStrip locale={locale} items={spotlightsAt("after_low_stock")} />
    <EditorialPreview articles={editorial} locale={locale} href={`/${locale}/knowledge`} />
    <section className="home-quote-cta site-container"><aside className="home-quote-media" aria-hidden="true"><Image src="/images/mehrasl-banner-1200x430.jpg" alt="" fill sizes="100vw" /></aside><div><span>{english ? "Industrial purchasing" : "ویژه پیمانکاران، شرکت‌ها و همکاران"}</span><h2>{english ? "Contact us about availability and pricing" : "برای خرید پروژه‌ای، مسیر جدا داریم."}</h2><p>{english ? "Send the technical specification or product code you need." : "فهرست نیازتان را آماده کنید؛ استعلام قیمت و بررسی فنی از همین‌جا شروع می‌شود."}</p></div><div><Link className="primary" href={`/${locale}/rfq`}>{english ? "Request an inquiry" : "استعلام قیمت"}</Link><Link className="secondary" href={`/${locale}/shop`}>{english ? "Browse products" : "مشاهده محصولات"}</Link></div></section>
  </main>;
}
