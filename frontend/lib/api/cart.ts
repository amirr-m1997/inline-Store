import { apiRequest } from "./client";

export type CartSummary = { guest_token: string | null; items: { quantity: number }[] };
export type CartItemResult = { guest_token?: string | null };

export function getCart<T = CartSummary>(signal?: AbortSignal) {
  return apiRequest<T>("/api/v1/cart/", { cache: "no-store", guestCart: true, signal });
}

export function addItem(productId: number, quantity: number) {
  return apiRequest<CartItemResult>("/api/v1/cart/items/", { method: "POST", guestCart: true, body: { product_id: productId, quantity } });
}

export function updateItem(itemId: number, quantity: number) {
  return apiRequest<CartItemResult>(`/api/v1/cart/items/${itemId}/`, { method: "PATCH", guestCart: true, body: { quantity } });
}

export function removeItem(itemId: number) {
  return apiRequest<null>(`/api/v1/cart/items/${itemId}/`, { method: "DELETE", guestCart: true });
}

export function updateCart<T>(body: unknown) { return apiRequest<T>("/api/v1/cart/", { method: "PATCH", guestCart: true, body }); }
export function checkout<T>() { return apiRequest<T>("/api/v1/cart/checkout/", { method: "POST", guestCart: true }); }
export function applyDiscount<T>(code: string) { return apiRequest<T>("/api/v1/cart/discount/", { method: "POST", guestCart: true, body: { code } }); }
export function removeDiscount<T>() { return apiRequest<T>("/api/v1/cart/discount/", { method: "DELETE", guestCart: true }); }
