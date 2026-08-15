import { apiRequest } from "./client";

const backendUrl = () => process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function getServer<T>(path: string): Promise<T> {
  const response = await fetch(`${backendUrl()}${path}`, { next: { revalidate: 60 } });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(`CONTENT_REQUEST_FAILED:${response.status}`);
  return data as T;
}

export function getCompany<T>() { return apiRequest<T>("/api/v1/company/", { cache: "no-store" }); }
export function getHero<T>() { return apiRequest<T>("/api/v1/site/hero/", { cache: "no-store" }); }
export function getAdvantages<T>() { return apiRequest<T>("/api/v1/site/advantages/", { cache: "no-store" }); }
export function getNavigation<T>() { return apiRequest<T>("/api/v1/site/navigation/"); }
export function getFooter<T>() { return apiRequest<T>("/api/v1/site/footer/", { cache: "no-store" }); }
export function getSupplyBrands<T>() { return apiRequest<T>("/api/v1/supply-brands/"); }
export function sendContact<T>(body: unknown) { return apiRequest<T>("/api/v1/site/contact/", { method: "POST", body }); }
export function getWarrantyPolicy<T>() { return apiRequest<T | null>("/api/v1/site/support/warranty-policy/"); }
export function submitSupport<T>(body: unknown) { return apiRequest<T>("/api/v1/site/support/requests/", { method: "POST", body }); }
export function getSupportRequests<T>() { return apiRequest<T[]>("/api/v1/site/support/requests/"); }
export function submitWarranty<T>(body: unknown) { return apiRequest<T>("/api/v1/site/support/warranty-registrations/", { method: "POST", body }); }
export function getWarrantyRegistrations<T>() { return apiRequest<T[]>("/api/v1/site/support/warranty-registrations/"); }
export function submitFeedback<T>(body: unknown) { return apiRequest<T>("/api/v1/site/support/feedback/", { method: "POST", body }); }

export const getCompanyServer = <T,>() => getServer<T>("/api/v1/company/");
export const getHeroServer = <T,>() => getServer<T>("/api/v1/site/hero/");
export const getAdvantagesServer = <T,>() => getServer<T>("/api/v1/site/advantages/");
export const getSupplyBrandsServer = <T,>() => getServer<T>("/api/v1/supply-brands/");
export const getFooterServer = <T,>() => getServer<T>("/api/v1/site/footer/");
export const getCompanySectionsServer = <T,>() => getServer<T>("/api/v1/company/sections/");
export const getCapabilitiesServer = <T,>() => getServer<T>("/api/v1/company/capabilities/");
export const getCapabilityServer = <T,>(slug: string) => getServer<T>(`/api/v1/company/capabilities/${encodeURIComponent(slug)}/`);
export const getCompanyLocationsServer = <T,>() => getServer<T>("/api/v1/company/locations/");
export const getCompanyMilestonesServer = <T,>() => getServer<T>("/api/v1/company/milestones/");
export const getCompanyCertificationsServer = <T,>() => getServer<T>("/api/v1/company/certifications/");
export const getCompanyHonorsServer = <T,>() => getServer<T>("/api/v1/company/honors/");
export const getIndustriesServer = <T,>() => getServer<T>("/api/v1/company/industries/");
export const getIndustryServer = <T,>(slug: string) => getServer<T>(`/api/v1/company/industries/${encodeURIComponent(slug)}/`);
