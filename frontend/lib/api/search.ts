import type { EditorialArticle, FAQEntry } from "../../types/api";

export type SiteSearchProduct = { id: number; slug: string; code: string; name: string; name_fa: string; name_en: string; unit: string; image: string | null; category: { id: number; slug: string; name_fa: string; name_en: string } | null; brand: { id: number; slug: string; name: string } | null };
export type SiteSearchCategory = { id: number; slug: string; name: string; name_fa: string; name_en: string; image: string | null; product_count: number };
export type SiteSearchBrand = { id: number; slug: string; name: string; logo: string | null; product_count: number };
export type SiteSearchResponse = { query: string; products: SiteSearchProduct[]; categories: SiteSearchCategory[]; brands: SiteSearchBrand[]; articles: EditorialArticle[]; faqs: FAQEntry[]; counts: { products: number; categories: number; brands: number; articles: number; faqs: number } };

function queryString(parameters: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => { if (value !== undefined && value !== "") query.set(key, String(value)); });
  return query.toString();
}

export async function getSiteSearchServer(query: string, locale: string): Promise<SiteSearchResponse> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}/api/v1/search/?${queryString({ q: query, lang: locale })}`, { next: { revalidate: 15 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`SEARCH_REQUEST_FAILED:${response.status}`);
  return data as SiteSearchResponse;
}
