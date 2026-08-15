import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getProductServer, type ProductDetail } from "../../../../lib/api/products";
import { toProductDetail } from "../../../../lib/product/adapters";
import { ProductDetailInteractive } from "../../../../components/product/detail/product-detail-interactive";
import { ProductTabs } from "../../../../components/product/detail/product-tabs";
import { ProductIdentity } from "../../../../components/product/detail/product-identity";
import { ProductSpecifications } from "../../../../components/product/detail/product-specifications";
import { ProductDocuments } from "../../../../components/product/detail/product-documents";
import { ProductRelationships } from "../../../../components/product/detail/product-relationships";
import Link from "next/link";
import { getCategoryUrl } from "../../../../lib/category-url";
import { absoluteUrl, localizedAlternates, localizedPath } from "../../../../lib/locale-url";

type RouteParams = { locale: string; slug: string };

async function loadProduct(slug: string) {
  try { return await getProductServer(slug); } catch (error) { if (error instanceof Error && error.message === "PRODUCT_NOT_FOUND") notFound(); throw error; }
}

export async function generateMetadata({ params }: { params: Promise<RouteParams> }): Promise<Metadata> {
  const { locale, slug } = await params;
  const product = await loadProduct(slug);
  const title = product.name_fa;
  const path = `/product/${encodeURIComponent(slug)}`;
  return { title, description: product.description || title, alternates: { canonical: absoluteUrl(localizedPath(locale, path)), ...localizedAlternates(path) }, openGraph: { title, description: product.description || title, type: "website", locale } };
}

function structuredData(product: ProductDetail, locale: string) {
  const productUrl = absoluteUrl(localizedPath(locale, `/product/${encodeURIComponent(product.slug)}`));
  const productData: Record<string, unknown> = { "@context": "https://schema.org", "@type": "Product", name: product.name_fa, sku: product.sku, url: productUrl };
  if (product.description) productData.description = product.description;
  if (product.images.length) productData.image = product.images.map((image) => image.url);
  if (product.category_tree.length) productData.category = product.category_tree.at(-1)?.name_fa;
  if (product.pricing.final_price && product.pricing.currency) productData.offers = { "@type": "Offer", price: product.pricing.final_price, priceCurrency: product.pricing.currency, availability: product.inventory.allowed_for_cart > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock", url: productUrl };
  const breadcrumbItems = [{ "@type": "ListItem", position: 1, name: "خانه", item: absoluteUrl(localizedPath(locale)) }, ...product.category_tree.map((category, index) => ({ "@type": "ListItem", position: index + 2, name: category.name_fa, item: absoluteUrl(getCategoryUrl(category, locale)) })), { "@type": "ListItem", position: product.category_tree.length + 2, name: product.name_fa, item: productUrl }];
  return [productData, { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: breadcrumbItems }];
}

export default async function ProductPage({ params }: { params: Promise<RouteParams> }) {
  const { locale, slug } = await params;
  const product = await loadProduct(slug);
  const domainProduct = toProductDetail(product);
  const jsonLd = structuredData(product, locale);
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} /><main className="product-detail-page site-container" dir={locale === "fa" ? "rtl" : "ltr"}>
    <nav className="product-breadcrumb" aria-label="مسیر صفحه"><Link href={`/${locale}`}>خانه</Link>{product.category_tree.map((category) => <span className="breadcrumb-part" key={category.id}><span>/</span><Link href={getCategoryUrl(category, locale)}>{category.name_fa}</Link></span>)}<span>/</span><b>{product.name_fa}</b></nav>
    <section className="product-purchase-layout"><ProductDetailInteractive product={product} domainProduct={domainProduct} identity={<ProductIdentity product={domainProduct} />} /></section>
    <nav className="product-support-actions" aria-label={locale === "en" ? "Product support" : "پشتیبانی محصول"}><span>{locale === "en" ? "Need help with this product?" : "برای این محصول به راهنمایی نیاز دارید؟"}</span><Link href={`/${locale}/support/request?product=${encodeURIComponent(product.slug)}`}>{locale === "en" ? "Product support" : "پشتیبانی محصول"}</Link><Link href={`/${locale}/support/warranty?product=${encodeURIComponent(product.slug)}`}>{locale === "en" ? "Warranty information" : "اطلاعات گارانتی"}</Link></nav>
    <ProductTabs description={product.description} specifications={<ProductSpecifications product={domainProduct} />} />
    <ProductDocuments product={domainProduct} /><ProductRelationships product={domainProduct} locale={locale} />
  </main></>;
}
