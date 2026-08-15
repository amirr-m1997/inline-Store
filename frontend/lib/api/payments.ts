import { apiRequest } from "./client";

export function getPayment<T>(id: string, signal?: AbortSignal) { return apiRequest<T>(`/api/v1/orders/payments/${id}/`, { cache: "no-store", guestCart: true, signal }); }
export function completeMockPayment<T>(id: string, outcome: "success" | "cancelled") { return apiRequest<T>(`/api/v1/orders/payments/${id}/mock-complete/`, { method: "POST", guestCart: true, body: { outcome } }); }
