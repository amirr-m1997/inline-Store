import { apiRequest } from "./client";

export function saveCheckoutCustomer<T>(customer: unknown) {
  return apiRequest<T>("/api/v1/cart/", { method: "PATCH", guestCart: true, body: { customer, save_to_profile: true } });
}

export function initializeCheckout<T>() {
  return apiRequest<T>("/api/v1/cart/checkout/", { method: "POST", guestCart: true });
}
