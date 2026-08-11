import { CatalogExplorer } from "../../../components/catalog/catalog-explorer";

export default async function ShopPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  return <CatalogExplorer slug="shop" query={q} />;
}
