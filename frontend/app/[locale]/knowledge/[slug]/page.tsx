import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EditorialContextSections, demoLabel, formatEditorialDate, localizedText, typeLabel } from "../../../../components/content/editorial";
import { ArticleDiscovery } from "../../../../components/content/discovery";
import { getArticleDiscoveryServer, getArticleServer } from "../../../../lib/api/content";
import type { EditorialArticle } from "../../../../types/api";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../lib/locale-url";

type RouteParams = { locale: string; slug: string };
async function loadArticle(slug: string) { try { return await getArticleServer(slug); } catch (error) { if (error instanceof Error && error.message === "CONTENT_REQUEST_FAILED:404") notFound(); throw error; } }
function jsonLd(value: unknown) { return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(value).replace(/</g, "\\u003c") }} />; }

export async function generateMetadata({ params }: { params: Promise<RouteParams> }): Promise<Metadata> {
  const { locale, slug } = await params; const article = await loadArticle(slug); const title = localizedText(article, locale, "seo_title") || localizedText(article, locale, "title"); const description = localizedText(article, locale, "seo_description") || localizedText(article, locale, "excerpt"); const path = `/knowledge/${encodeURIComponent(slug)}`;
  return { title, description: description || undefined, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(`/knowledge/${encodeURIComponent(slug)}`) }, openGraph: { title, description: description || undefined, url: absoluteUrl(localizedPath(locale, path)), locale: locale === "en" ? "en_US" : "fa_IR", type: article.content_type === "news" ? "article" : "article" } };
}

function articleType(article: EditorialArticle) { if (article.content_type === "news") return "NewsArticle"; if (article.content_type === "technical_article") return "TechArticle"; return "Article"; }

export default async function EditorialArticlePage({ params }: { params: Promise<RouteParams> }) {
  const { locale, slug } = await params; const article = await loadArticle(slug); const english = locale === "en"; const title = localizedText(article, locale, "title"); const excerpt = localizedText(article, locale, "excerpt"); const body = localizedText(article, locale, "body"); const categoryTitle = article.category ? (english && article.category.name_en ? article.category.name_en : article.category.name_fa) : null;
  const discovery = await getArticleDiscoveryServer(article.slug).catch(() => ({ articles: [], faqs: [], resources: [], products: [] })); const path = `/knowledge/${encodeURIComponent(slug)}`; const articleUrl = absoluteUrl(localizedPath(locale, path));
  const structured = [{ "@context": "https://schema.org", "@type": articleType(article), headline: title, description: excerpt || undefined, datePublished: article.published_at || undefined, image: article.featured_image ? [article.featured_image] : undefined, mainEntityOfPage: articleUrl }, { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: english ? "Home" : "خانه", item: absoluteUrl(localizedPath(locale)) }, { "@type": "ListItem", position: 2, name: english ? "Knowledge & News" : "دانش و اخبار", item: absoluteUrl(localizedPath(locale, "/knowledge")) }, { "@type": "ListItem", position: 3, name: title, item: articleUrl }] }];
  const discoveryForArticle = article.related_products?.length ? { ...discovery, products: [] } : discovery;
  return <>{jsonLd(structured)}<main className="editorial-detail-page site-container"><nav className="public-breadcrumb" aria-label={english ? "Breadcrumb" : "مسیر صفحه"}><Link href={`/${locale}`}>{english ? "Home" : "خانه"}</Link><span aria-hidden="true">/</span><Link href={`/${locale}/knowledge`}>{english ? "Knowledge & News" : "دانش و اخبار"}</Link><span aria-hidden="true">/</span><b>{title}</b></nav><article className="editorial-article"><header className="editorial-article-header"><div className="editorial-article-meta"><span>{typeLabel(article, locale)}</span>{categoryTitle && <Link href={`/${locale}/knowledge?category=${encodeURIComponent(article.category!.slug)}`}>{categoryTitle}</Link>}{article.published_at && <time dateTime={article.published_at}>{formatEditorialDate(article.published_at, locale)}</time>}</div><h1>{title} {demoLabel(title, locale)}</h1>{excerpt && <p>{excerpt}</p>}</header>{article.featured_image && <img className="editorial-article-image" src={article.featured_image} alt="" />}{body && <div className="editorial-article-body">{body}</div>}<EditorialContextSections article={article} locale={locale} /><ArticleDiscovery discovery={discoveryForArticle} locale={locale} /></article></main></>;
}
