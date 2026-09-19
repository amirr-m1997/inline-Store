import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getProductDiscoveryServer, getProductServer, type ProductDetail } from "../../../../lib/api/products";
import { toProductDetail } from "../../../../lib/product/adapters";
import { ProductDetailInteractive } from "../../../../components/product/detail/product-detail-interactive";
import { ProductTabs } from "../../../../components/product/detail/product-tabs";
import { ProductIdentity } from "../../../../components/product/detail/product-identity";
import { ProductSpecifications } from "../../../../components/product/detail/product-specifications";
import { ProductDocuments } from "../../../../components/product/detail/product-documents";
import { ProductRelationships } from "../../../../components/product/detail/product-relationships";
import { ProductReviews } from "../../../../components/product/detail/product-reviews";
import { ProductQuestions } from "../../../../components/product/detail/product-questions";
import Link from "next/link";
import { getCategoryUrl } from "../../../../lib/category-url";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../lib/locale-url";
import { EditorialPreview, FAQList } from "../../../../components/content/editorial";
import { DiscoveryResources } from "../../../../components/content/discovery";

type RouteParams = { locale: string; slug: string };

const stripHtml = (value: string) => value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();

async function loadProduct(slug: string) {
  try { return await getProductServer(slug); } catch (error) { if (error instanceof Error && error.message === "PRODUCT_NOT_FOUND") notFound(); throw error; }
}

export async function generateMetadata({ params }: { params: Promise<RouteParams> }): Promise<Metadata> {
  const { locale, slug } = await params;
  const product = await loadProduct(slug);
  const title = locale === "en" && product.name_en ? product.name_en : product.name_fa;
  const description = (stripHtml(product.description || "") || title).slice(0, 160);
  const path = `/product/${encodeURIComponent(slug)}`;
  return { title, description, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description, type: "website", locale: locale === "en" ? "en_US" : "fa_IR" } };
}

function structuredData(product: ProductDetail, locale: string) {
  const productUrl = absoluteUrl(localizedPath(locale, `/product/${encodeURIComponent(product.slug)}`));
  const productData: Record<string, unknown> = { "@context": "https://schema.org", "@type": "Product", name: product.name_fa, sku: product.sku, url: productUrl };
  if (product.description) productData.description = stripHtml(product.description);
  if (product.images.length) productData.image = product.images.map((image) => image.url);
  if (product.category_tree.length) productData.category = product.category_tree.at(-1)?.name_fa;
  if (product.brand?.name) productData.brand = { "@type": "Brand", name: product.brand.name };
  if (product.pricing.final_price && product.pricing.currency) productData.offers = { "@type": "Offer", price: product.pricing.final_price, priceCurrency: product.pricing.currency === "ریال" ? "IRR" : product.pricing.currency, availability: product.inventory.allowed_for_cart > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock", url: productUrl };
  const breadcrumbItems = [{ "@type": "ListItem", position: 1, name: locale === "en" ? "Home" : "خانه", item: absoluteUrl(localizedPath(locale)) }, ...product.category_tree.map((category, index) => ({ "@type": "ListItem", position: index + 2, name: category.name_fa, item: absoluteUrl(getCategoryUrl(category, locale)) })), { "@type": "ListItem", position: product.category_tree.length + 2, name: locale === "en" && product.name_en ? product.name_en : product.name_fa, item: productUrl }];
  return [productData, { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: breadcrumbItems }];
}

export default async function ProductPage({ params }: { params: Promise<RouteParams> }) {
  const { locale, slug } = await params;
  const product = await loadProduct(slug);
  const discovery = await getProductDiscoveryServer(slug).catch(() => ({ articles: [], faqs: [], resources: [], products: [] }));
  const domainProduct = toProductDetail(product);
  const jsonLd = structuredData(product, locale);
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} /><main className="product-detail-page site-container" dir={locale === "fa" ? "rtl" : "ltr"}>
    <nav className="product-breadcrumb" aria-label={locale === "en" ? "Page path" : "مسیر صفحه"}><Link href={`/${locale}`}>{locale === "en" ? "Home" : "خانه"}</Link>{product.category_tree.map((category) => <span className="breadcrumb-part" key={category.id}><span>/</span><Link href={getCategoryUrl(category, locale)}>{category.name_fa}</Link></span>)}<span>/</span><b>{product.name_fa}</b></nav>
    <section className="product-purchase-layout"><ProductDetailInteractive product={product} domainProduct={domainProduct} identity={<ProductIdentity product={domainProduct} />} /></section>
    <nav className="product-support-actions" aria-label={locale === "en" ? "Product support and quotation" : "پشتیبانی و استعلام محصول"}><span>{locale === "en" ? "Need help or a business quote?" : "برای این محصول به راهنمایی یا استعلام نیاز دارید؟"}</span><Link className="product-rfq-link" href={`/${locale}/rfq?product=${encodeURIComponent(product.slug)}`}>{locale === "en" ? "Request a Quote" : "استعلام قیمت"}</Link><Link href={`/${locale}/support/request?product=${encodeURIComponent(product.slug)}`}>{locale === "en" ? "Product support" : "پشتیبانی محصول"}</Link><Link href={`/${locale}/support/warranty?product=${encodeURIComponent(product.slug)}`}>{locale === "en" ? "Warranty information" : "اطلاعات گارانتی"}</Link></nav>
    <ProductTabs description={product.description} specifications={<ProductSpecifications product={domainProduct} />} />
    <ProductReviews productId={product.id} />
    <ProductQuestions productId={product.id} />
    <ProductDocuments product={domainProduct} /><DiscoveryResources resources={discovery.resources} locale={locale} /><ProductRelationships product={domainProduct} locale={locale} /><FAQList faqs={discovery.faqs} locale={locale} compact title={locale === "en" ? "Product FAQs" : "سوالات متداول این محصول"} /><EditorialPreview articles={discovery.articles} locale={locale} title={locale === "en" ? "Related Articles" : "مطالب مرتبط"} />
  </main></>;
}
