import { apiRequest } from "./client";

export type OrderSummary = { id: number; order_number: string; status_label: string; created_at: string; final_amount: string; items_count: number };

export function getOrders<T = OrderSummary[]>() {
  return apiRequest<T>("/api/customer/orders/", { cache: "no-store" });
}

export function getOrder<T>(id: string | number) { return apiRequest<T>(`/api/customer/orders/${id}/`, { cache: "no-store" }); }
export function sendInvoice<T>(id: string | number) { return apiRequest<T>(`/api/customer/orders/${id}/invoice/send/`, { method: "POST" }); }
export function requestProforma<T>(id: string | number, note: string) { return apiRequest<T>(`/api/customer/orders/${id}/proforma/request/`, { method: "POST", body: { note } }); }
