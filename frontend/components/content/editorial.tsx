import Link from "next/link";
import type { EditorialArticle, EditorialCategory } from "../../types/api";
import type { FAQEntry } from "../../types/api";

export const editorialTypes = [
  { value: "", fa: "همه", en: "All" },
  { value: "news", fa: "اخبار", en: "News" },
  { value: "event", fa: "رویدادها", en: "Events" },
  { value: "technical_article", fa: "مقالات فنی", en: "Technical Articles" },
  { value: "product_guide", fa: "راهنمای محصول", en: "Product Guides" },
  { value: "buying_guide", fa: "راهنمای انتخاب", en: "Buying Guides" },
  { value: "product_announcement", fa: "معرفی محصول", en: "Product Announcements" },
] as const;

export const newsTypes = new Set(["news", "event", "product_announcement"]);

export function localizedText(article: EditorialArticle, locale: string, field: "title" | "excerpt" | "body" | "seo_title" | "seo_description") {
  const english = locale === "en";
  const preferred = english ? article[`${field}_en` as keyof EditorialArticle] : article[`${field}_fa` as keyof EditorialArticle];
  const fallback = english ? article[`${field}_fa` as keyof EditorialArticle] : article[`${field}_en` as keyof EditorialArticle];
  return (typeof preferred === "string" && preferred) || (typeof fallback === "string" && fallback) || (field === "title" ? article.title : field === "excerpt" ? article.excerpt : field === "body" ? article.body || "" : "");
}

export function typeLabel(article: EditorialArticle, locale: string) {
  const item = editorialTypes.find((entry) => entry.value === article.content_type);
  return item ? (locale === "en" ? item.en : item.fa) : article.content_type_label || article.content_type;
}

export function formatEditorialDate(value: string | null, locale: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(locale === "en" ? "en-US" : "fa-IR", { dateStyle: "medium" }).format(date);
}

export function demoLabel(title: string, locale: string) {
  return process.env.NODE_ENV !== "production" && title.startsWith("[DEMO]") ? <span className="content-demo-indicator">{locale === "en" ? "Demo" : "نمونه"}</span> : null;
}

export function isDemoArticle(article: EditorialArticle) {
  return article.title_fa.startsWith("[DEMO]") || article.title_en.startsWith("[DEMO]") || article.title.startsWith("[DEMO]");
}

export function EditorialCard({ article, locale, variant = "standard" }: { article: EditorialArticle; locale: string; variant?: "featured" | "standard" | "compact" }) {
  const title = localizedText(article, locale, "title");
  const excerpt = localizedText(article, locale, "excerpt");
  const type = typeLabel(article, locale);
  const href = `/${locale}/knowledge/${encodeURIComponent(article.slug)}`;
  return <article className={`editorial-card editorial-card--${variant}`}>
    {article.featured_image && <Link className="editorial-card-media" href={href} aria-label={`${locale === "en" ? "Read" : "مطالعه"} ${title}`}><img src={article.featured_image} alt="" loading={variant === "featured" ? "eager" : "lazy"} /></Link>}
    <div className="editorial-card-body"><div className="editorial-card-meta"><span>{type}</span>{article.category && <span>{locale === "en" && article.category.name_en ? article.category.name_en : article.category.name_fa}</span>}{article.published_at && <time dateTime={article.published_at}>{formatEditorialDate(article.published_at, locale)}</time>}</div><h2><Link href={href}>{title}</Link> {demoLabel(title, locale)}</h2>{excerpt && <p>{excerpt}</p>}<Link className="editorial-read-link" href={href}>{locale === "en" ? "Read article" : "مطالعه مطلب"}<span aria-hidden="true">←</span></Link></div>
  </article>;
}

export function EditorialTypeNav({ locale, basePath, selectedType = "", allowedTypes }: { locale: string; basePath: string; selectedType?: string; allowedTypes?: ReadonlySet<string> }) {
  const labels = editorialTypes.filter((item) => !allowedTypes || !item.value || allowedTypes.has(item.value));
  return <nav className="editorial-type-nav" aria-label={locale === "en" ? "Editorial content types" : "نوع محتوای تحریریه"}>{labels.map((item) => { const href = item.value ? `${basePath}?type=${encodeURIComponent(item.value)}` : basePath; return <Link key={item.value || "all"} className={selectedType === item.value ? "is-active" : undefined} href={href} aria-current={selectedType === item.value ? "page" : undefined}>{locale === "en" ? item.en : item.fa}</Link>; })}</nav>;
}

export function EditorialPreview({ articles, locale, title, href }: { articles: EditorialArticle[]; locale: string; title?: string; href?: string }) {
  if (!articles.length) return null;
  const heading = title || (locale === "en" ? "Knowledge & News" : "دانش و اخبار");
  return <section className="editorial-preview site-container" aria-labelledby="editorial-preview-title"><header><div><span>{locale === "en" ? "Editorial perspective" : "نگاه تحریریه"}</span><h2 id="editorial-preview-title">{heading}</h2></div>{href && <Link href={href}>{locale === "en" ? "View all" : "مشاهده همه"}<span aria-hidden="true">←</span></Link>}</header><div className="editorial-preview-grid">{articles.slice(0, 3).map((article, index) => <EditorialCard key={article.id} article={article} locale={locale} variant={index === 0 ? "featured" : "compact"} />)}</div></section>;
}

export function EditorialContextSections({ article, locale }: { article: EditorialArticle; locale: string }) {
  const sections = [
    { key: "products", title: locale === "en" ? "Related Products" : "محصولات مرتبط", items: article.related_products.map((item) => ({ id: item.id, label: item.name, href: `/${locale}/product/${item.slug}` })) },
    { key: "categories", title: locale === "en" ? "Related Categories" : "دسته‌بندی‌های مرتبط", items: article.related_catalog_categories.map((item) => ({ id: item.id, label: locale === "en" && item.name_en ? item.name_en : item.name_fa, href: `/${locale}/category/${item.slug}` })) },
    { key: "industries", title: locale === "en" ? "Related Industries" : "صنایع مرتبط", items: article.related_industries.map((item) => ({ id: item.id, label: locale === "en" && item.name_en ? item.name_en : item.name_fa, href: `/${locale}/industries/${item.slug}` })) },
    { key: "capabilities", title: locale === "en" ? "Related Capabilities" : "توانمندی‌های مرتبط", items: article.related_capabilities.map((item) => ({ id: item.id, label: locale === "en" && item.title_en ? item.title_en : item.title_fa, href: `/${locale}/capabilities/${item.slug}` })) },
    { key: "brands", title: locale === "en" ? "Related Brands" : "برندهای مرتبط", items: article.related_brands.map((item) => ({ id: item.id, label: item.name, href: item.slug ? `/${locale}/brands/${item.slug}` : "" })) },
  ] as const;
  return <>{sections.filter((section) => section.items.length).map((section) => <section className="editorial-context-section" key={section.key} aria-labelledby={`editorial-${section.key}-title`}><h2 id={`editorial-${section.key}-title`}>{section.title}</h2><div className="editorial-context-links">{section.items.map((item) => item.href ? <Link key={item.id} href={item.href}>{item.label}<span aria-hidden="true">←</span></Link> : <span key={item.id}>{item.label}</span>)}</div></section>)}</>;
}

export function EditorialCategoryList({ categories, locale }: { categories: EditorialCategory[]; locale: string }) {
  if (!categories.length) return null;
  return <section className="editorial-topic-list" aria-labelledby="editorial-topics-title"><header><span>{locale === "en" ? "Browse by topic" : "کشف بر اساس موضوع"}</span><h2 id="editorial-topics-title">{locale === "en" ? "Editorial topics" : "موضوع‌های محتوایی"}</h2></header><div>{categories.map((category) => <Link key={category.id} href={`/${locale}/knowledge?category=${encodeURIComponent(category.slug)}`}>{locale === "en" && category.name_en ? category.name_en : category.name_fa}</Link>)}</div></section>;
}

export const faqTypes = [
  { value: "", fa: "همه", en: "All" },
  { value: "general", fa: "عمومی", en: "General" },
  { value: "product", fa: "محصول", en: "Product" },
  { value: "technical", fa: "فنی", en: "Technical" },
  { value: "warranty", fa: "گارانتی", en: "Warranty" },
  { value: "ordering", fa: "سفارش", en: "Ordering" },
  { value: "support", fa: "پشتیبانی", en: "Support" },
  { value: "installation", fa: "نصب", en: "Installation" },
  { value: "maintenance", fa: "نگهداری", en: "Maintenance" },
] as const;

export function faqTypeLabel(faq: FAQEntry, locale: string) {
  const item = faqTypes.find((entry) => entry.value === faq.faq_type);
  return item ? (locale === "en" ? item.en : item.fa) : faq.faq_type_label || faq.faq_type;
}

export function localizedFAQ(faq: FAQEntry, locale: string, field: "question" | "answer") {
  const preferred = locale === "en" ? faq[`${field}_en`] : faq[`${field}_fa`];
  const fallback = locale === "en" ? faq[`${field}_fa`] : faq[`${field}_en`];
  return preferred || fallback || faq[field];
}

export function FAQContextLinks({ faq, locale }: { faq: FAQEntry; locale: string }) {
  const links = [
    ...faq.related_products.slice(0, 2).map((item) => ({ key: `product-${item.id}`, label: item.name, href: `/${locale}/product/${item.slug}` })),
    ...faq.related_categories.slice(0, 2).map((item) => ({ key: `category-${item.id}`, label: locale === "en" && item.name_en ? item.name_en : item.name_fa, href: `/${locale}/category/${item.slug}` })),
    ...faq.related_industries.slice(0, 2).map((item) => ({ key: `industry-${item.id}`, label: locale === "en" && item.name_en ? item.name_en : item.name_fa, href: `/${locale}/industries/${item.slug}` })),
    ...faq.related_capabilities.slice(0, 2).map((item) => ({ key: `capability-${item.id}`, label: locale === "en" && item.title_en ? item.title_en : item.title_fa, href: `/${locale}/capabilities/${item.slug}` })),
    ...faq.related_articles.slice(0, 1).map((item) => ({ key: `article-${item.id}`, label: locale === "en" && item.title_en ? item.title_en : item.title_fa, href: `/${locale}/knowledge/${item.slug}#faq-${faq.slug}` })),
  ];
  if (!links.length) return null;
  return <div className="faq-context-links" aria-label={locale === "en" ? "Related context" : "زمینه مرتبط"}>{links.map((item) => <Link key={item.key} href={item.href}>{item.label}</Link>)}</div>;
}

export function FAQList({ faqs, locale, title, compact = false }: { faqs: FAQEntry[]; locale: string; title?: string; compact?: boolean }) {
  if (!faqs.length) return null;
  return <section className={`faq-list${compact ? " faq-list--compact" : ""}`} aria-labelledby={title ? "faq-list-title" : undefined}>{title && <header><span>{locale === "en" ? "Technical knowledge" : "دانش فنی"}</span><h2 id="faq-list-title">{title}</h2></header>}<div className="faq-disclosures">{faqs.map((faq) => <details className="faq-disclosure" key={faq.id} id={`faq-${faq.slug}`}><summary><span><small>{faqTypeLabel(faq, locale)}</small>{localizedFAQ(faq, locale, "question")}</span><b aria-hidden="true">+</b></summary><div className="faq-answer"><p>{localizedFAQ(faq, locale, "answer")}</p><FAQContextLinks faq={faq} locale={locale} /></div></details>)}</div></section>;
}

export function EditorialPagination({ locale, basePath, page, hasNext, query }: { locale: string; basePath: string; page: number; hasNext: boolean; query?: Record<string, string> }) {
  if (page <= 1 && !hasNext) return null;
  const href = (nextPage: number) => {
    const params = new URLSearchParams(query);
    if (nextPage > 1) params.set("page", String(nextPage)); else params.delete("page");
    const suffix = params.toString();
    return `${basePath}${suffix ? `?${suffix}` : ""}`;
  };
  return <nav className="editorial-pagination" aria-label={locale === "en" ? "Editorial pagination" : "صفحه‌بندی مطالب"}>
    {page > 1 && <Link href={href(page - 1)}>{locale === "en" ? "Previous" : "قبلی"}</Link>}
    <span>{locale === "en" ? `Page ${page}` : `صفحه ${page}`}</span>
    {hasNext && <Link href={href(page + 1)}>{locale === "en" ? "Next" : "بعدی"}</Link>}
  </nav>;
}
