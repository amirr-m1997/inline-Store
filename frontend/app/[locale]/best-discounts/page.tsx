import { CatalogExplorer } from "../../../components/catalog/catalog-explorer";
import { catalogMetadata, catalogStructuredData, loadCatalogInitial, type CatalogRouteSearch } from "../../../lib/catalog-server";

type Props = { params: Promise<{ locale: string }>; searchParams: Promise<CatalogRouteSearch> };
export default async function BestDiscountsPage({ params, searchParams }: Props) { const [{ locale }, currentSearchParams] = await Promise.all([params, searchParams]); const initial = await loadCatalogInitial("best-discounts", currentSearchParams); const jsonLd = catalogStructuredData("best-discounts", locale, null, initial.data); return <><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} /><CatalogExplorer slug="best-discounts" initialData={initial.data} /></>; }
export async function generateMetadata({ params, searchParams }: Props) { const [{ locale }, currentSearchParams] = await Promise.all([params, searchParams]); return catalogMetadata("best-discounts", locale, null, currentSearchParams); }
