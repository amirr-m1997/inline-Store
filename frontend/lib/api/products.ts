import type { CatalogProduct } from "../../components/catalog/product-card";
import { apiRequest } from "./client";

export type ProductPage = { count: number; results: CatalogProduct[] };
export type CatalogQueryFacetOption = { value: string; label: string; count?: number; selected?: boolean };
export type CatalogQueryFacet = { name: string; label?: string; type: "checkbox" | "single_select" | "boolean" | "range" | "hierarchical_category"; options?: CatalogQueryFacetOption[]; min?: number; max?: number; unit?: string; selected?: unknown };
export type CatalogQueryResponse = { products: CatalogProduct[]; facets: CatalogQueryFacet[]; applied_filters: Record<string, unknown>; next_cursor: string | null; previous_cursor: string | null; has_more: boolean; total_count: number; page?: number | null; next?: string | null; previous?: string | null };
export type CategoryTree = { id: number; name_fa: string; slug: string; has_children: boolean; product_count: number; children: CategoryTree[] };
export type ProductBrand = { id: number; name: string; code: string | null; slug: string; logo: string | null; description_fa: string; description_en: string; website: string; product_count: number; products?: { id: number; name: string; code: string; slug: string }[]; seo_title_fa: string; seo_title_en: string; seo_description_fa: string; seo_description_en: string };
export type ProductResource = { id: number; title: string; type: "datasheet" | "manual" | "cad" | "certificate" | "catalogue" | "other"; file_url: string; file_name: string; display_name: string; mime_type: string; size: number; revision: string; language: string; product: { id: number; name: string; code: string; slug: string } };
export type ProductResourcePage = { count: number; next: boolean; previous: boolean; results: ProductResource[] };
export type ProductDetail = {
  id: number; slug: string; name_fa: string; name_en: string; sku: string; unit: string; description: string;
  images: { id: number; url: string; alt_fa: string; alt_en: string; alt_text: string; is_primary: boolean }[];
  category_tree: { id: number; name_fa: string; slug: string }[];
  inventory: { available: number | null; reserved: number | null; net: number | null; allowed_for_cart: number; last_receipt_date: string | null; last_issue_date: string | null };
  pricing: { price: string | null; currency: string | null; discount_percentage: string | null; final_price: string | null; last_purchase_irr: string | null; receipt_usd_rate: string | null; last_purchase_usd: string | null; today_irr_equivalent: string | null };
  technical_specifications: { label: string; value: unknown }[];
  related_products: { id: number; slug: string; code: string; name_fa: string; unit: string; primary_image: string | null }[];
  service_advantages: { id: number; title_fa: string; title_en: string; description_fa: string; description_en: string; icon: string }[];
};
export type ProductDiscovery = {
  articles: import("../../types/api").EditorialArticle[];
  faqs: import("../../types/api").FAQEntry[];
  resources: ProductResource[];
  products: { id: number; slug: string; code: string; name_fa: string; unit: string; primary_image: string | null }[];
};

export function getProducts(parameters: Record<string, string | number | boolean | undefined>, signal?: AbortSignal) {
  const search = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  return apiRequest<ProductPage>(`/api/v1/products/?${search}`, { cache: "no-store", signal });
}

export async function getProductsServer(parameters: Record<string, string | number | boolean | undefined>): Promise<ProductPage> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const search = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  const response = await fetch(`${backendUrl}/api/v1/products/?${search}`, { next: { revalidate: 30 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`PRODUCTS_REQUEST_FAILED:${response.status}`);
  return data as ProductPage;
}

export function getCatalogQuery(parameters: Record<string, string | number | boolean | undefined>, signal?: AbortSignal) {
  const search = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  return apiRequest<CatalogQueryResponse>(`/api/v1/products/catalog-query/?${search}`, { cache: "no-store", signal });
}

export function getProduct(slug: string, signal?: AbortSignal) {
  return apiRequest<ProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(slug)}/`, { signal });
}

export async function getProductServer(slug: string): Promise<ProductDetail> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}/api/v1/catalog/products/${encodeURIComponent(slug)}/`, { next: { revalidate: 60, tags: [`product:${slug}`] } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(response.status === 404 ? "PRODUCT_NOT_FOUND" : "PRODUCT_REQUEST_FAILED");
  return data as ProductDetail;
}

export async function getProductDiscoveryServer(slug: string): Promise<ProductDiscovery> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(backendUrl + "/api/v1/catalog/products/" + encodeURIComponent(slug) + "/discovery/", { next: { revalidate: 60, tags: ["product-discovery:" + slug] } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error("PRODUCT_DISCOVERY_REQUEST_FAILED");
  return data as ProductDiscovery;
}

export async function getCatalogQueryServer(parameters: Record<string, string | number | boolean | undefined>): Promise<CatalogQueryResponse> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const search = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => { if (value !== undefined && value !== "") search.set(key, String(value)); });
  const response = await fetch(`${backendUrl}/api/v1/products/catalog-query/?${search}`, { next: { revalidate: 30 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(response.status === 404 ? "CATALOG_NOT_FOUND" : "CATALOG_REQUEST_FAILED");
  return data as CatalogQueryResponse;
}

export async function getCategoryServer(slug: string): Promise<CategoryRecord & { redirect_slug?: string }> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}/api/v1/catalog/categories/by-slug/${encodeURIComponent(slug)}/`, { next: { revalidate: 60 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(response.status === 404 ? "CATEGORY_NOT_FOUND" : "CATEGORY_REQUEST_FAILED");
  return data as CategoryRecord & { redirect_slug?: string };
}

export function getCategories(signal?: AbortSignal) {
  return apiRequest<CategoryTree[]>("/api/v1/categories/tree/", { signal });
}

export type CategoryRecord = { id: number; name_fa: string; slug: string; has_children: boolean };
export function getCategoryRoots<T = CategoryRecord[]>() { return apiRequest<T>("/api/v1/categories/roots/"); }
export async function getCategoryRootsServer<T = CategoryRecord[]>(): Promise<T> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}/api/v1/categories/roots/`, { next: { revalidate: 60 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`CATEGORIES_REQUEST_FAILED:${response.status}`);
  return data as T;
}
export function getCategoryChildren<T = CategoryRecord[]>(id: number) { return apiRequest<T>(`/api/v1/categories/children/${id}/`); }
export function getCategoryBySlug<T = CategoryRecord & { redirect_slug?: string }>(slug: string) { return apiRequest<T>(`/api/v1/categories/by-slug/${encodeURIComponent(slug)}/`); }
export async function getProductBrandsServer(): Promise<ProductBrand[]> { return getServerProducts<ProductBrand[]>("/api/v1/brands/"); }
export async function getProductBrandServer(slug: string): Promise<ProductBrand> { return getServerProducts<ProductBrand>(`/api/v1/brands/${encodeURIComponent(slug)}/`); }
export async function getProductDocumentsServer(parameters: Record<string, string | undefined> = {}): Promise<ProductResourcePage> { const query = new URLSearchParams(); Object.entries(parameters).forEach(([key, value]) => { if (value) query.set(key, value); }); return getServerProducts<ProductResourcePage>(`/api/v1/catalog/documents/${query.toString() ? `?${query}` : ""}`); }

async function getServerProducts<T>(path: string): Promise<T> {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${backendUrl}${path}`, { next: { revalidate: 60 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(response.status === 404 ? "BRAND_NOT_FOUND" : "BRANDS_REQUEST_FAILED");
  return data as T;
}
