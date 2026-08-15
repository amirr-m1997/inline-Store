import { notFound, redirect } from "next/navigation";
import { CatalogExplorer } from "../../../../components/catalog/catalog-explorer";
import { getCategoryUrl } from "../../../../lib/category-url";
import { catalogMetadata, catalogStructuredData, loadCatalogInitial, type CatalogInitialContext, type CatalogRouteSearch } from "../../../../lib/catalog-server";
import { getCategoryServer } from "../../../../lib/api/products";
import { getFAQsServer } from "../../../../lib/api/content";
import { FAQList } from "../../../../components/content/editorial";
import type { FAQEntry } from "../../../../types/api";

type Props = { params: Promise<{ locale: string; slug: string }>; searchParams: Promise<CatalogRouteSearch> };

export default async function CategoryPage({ params, searchParams }: Props) {
  const [{ locale, slug }, currentSearchParams] = await Promise.all([params, searchParams]);
  let initial: CatalogInitialContext;
  try {
    initial = await loadCatalogInitial(slug, currentSearchParams);
  } catch (error) { if (error instanceof Error && error.message === "CATEGORY_NOT_FOUND") notFound(); throw error; }
  if (initial.category?.redirect_slug) redirect(getCategoryUrl(initial.category, locale));
  const jsonLd = catalogStructuredData(slug, locale, initial.category, initial.data);
  const faqs = await getFAQsServer({ category: slug }).then((items) => items.slice(0, 4)).catch(() => [] as FAQEntry[]);
  return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} /><CatalogExplorer slug={slug} query={typeof currentSearchParams.q === "string" ? currentSearchParams.q : undefined} initialData={initial.data} initialCategory={initial.category} /><div className="site-container"><FAQList faqs={faqs} locale={locale} compact title={locale === "en" ? "Category FAQs" : "سوالات متداول این دسته‌بندی"} /></div></>;
}

export async function generateMetadata({ params, searchParams }: Props) { const [{ locale, slug }, currentSearchParams] = await Promise.all([params, searchParams]); let category: Awaited<ReturnType<typeof getCategoryServer>> | null = null; try { category = await getCategoryServer(slug); } catch (error) { if (error instanceof Error && error.message === "CATEGORY_NOT_FOUND") notFound(); throw error; } return catalogMetadata(slug, locale, category, currentSearchParams); }
