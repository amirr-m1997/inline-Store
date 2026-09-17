import { ProductComparePage } from "../../../components/catalog/product-compare-page";

export default async function ComparePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  return <ProductComparePage locale={locale} />;
}
