import { CatalogExplorer } from "../../../../components/catalog/catalog-explorer";

type CategoryPageProps = {
  params: Promise<{ locale: string; slug: string }>;
  searchParams: Promise<{ q?: string }>;
};

export default async function CategoryPage({ params, searchParams }: CategoryPageProps) {
  const [{ slug }, { q }] = await Promise.all([params, searchParams]);
  return <CatalogExplorer slug={slug} query={q} />;
}
