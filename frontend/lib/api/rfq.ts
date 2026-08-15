import { apiRequest } from "./client";

export type RfqProductSummary = { id: number; code: string; name: string; slug: string; unit: string };
export type RfqItem = { product: RfqProductSummary; requested_quantity: number; customer_note: string; product_code_snapshot: string; product_name_snapshot: string };
export type RfqRecord = {
  reference: string;
  company_name: string;
  contact_name: string;
  phone: string;
  email: string;
  subject: string;
  message: string;
  preferred_contact_method: string;
  status: string;
  created_at: string;
  updated_at: string;
  items: RfqItem[];
  quotation_reference: string | null;
  quotation_response: { response: string; response_at: string | null } | null;
};

export type QuotationItem = { product_name_snapshot: string; product_code_snapshot: string; quantity: number; unit_price: string; line_total: string };
export type QuotationResponse = { response: "pending" | "accepted" | "rejected" | "revision_requested"; note: string; response_at: string | null };
export type SalesQuotation = { reference: string; rfq_reference: string; status: string; currency: string; issued_at: string | null; expires_at: string | null; public_note: string; items: QuotationItem[]; subtotal: string; customer_response: QuotationResponse };

export type RfqItemInput = { product: number; requested_quantity: number; customer_note?: string };
export type RfqCreateInput = { company_name?: string; contact_name: string; phone?: string; email?: string; subject?: string; message?: string; preferred_contact_method?: string; items?: RfqItemInput[] };
export type RfqCartContextItem = { id: number; slug: string; name_fa: string; name_en: string; sku: string; code: string; unit: string; quantity: number };
export type RfqCartContext = { source: "cart"; items: RfqCartContextItem[]; omitted_count: number; max_items: number };

export function submitRfq(body: RfqCreateInput) { return apiRequest<RfqRecord>("/api/v1/rfq/", { method: "POST", body }); }
export function getRfqCartContext() { return apiRequest<RfqCartContext>("/api/v1/rfq/cart-context/", { cache: "no-store", guestCart: true }); }
export function getRfqs() { return apiRequest<RfqRecord[]>("/api/v1/rfq/", { cache: "no-store" }); }
export function getRfq(reference: string) { return apiRequest<RfqRecord>(`/api/v1/rfq/${encodeURIComponent(reference)}/`, { cache: "no-store" }); }
export function getQuotations() { return apiRequest<SalesQuotation[]>("/api/v1/rfq/quotations/", { cache: "no-store" }); }
export function getQuotation(reference: string) { return apiRequest<SalesQuotation>(`/api/v1/rfq/quotations/${encodeURIComponent(reference)}/`, { cache: "no-store" }); }
export function respondToQuotation(reference: string, response: Exclude<QuotationResponse["response"], "pending">, note = "") { return apiRequest<{ response: Exclude<QuotationResponse["response"], "pending">; response_at: string }>(`/api/v1/rfq/quotations/${encodeURIComponent(reference)}/respond/`, { method: "POST", body: { response, note } }); }
