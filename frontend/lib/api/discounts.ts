import { apiRequest } from "./client";

export function applyDiscount<T>(code: string) {
  return apiRequest<T>("/api/v1/cart/discount/", { method: "POST", guestCart: true, body: { code } });
}

export function removeDiscount<T>() {
  return apiRequest<T>("/api/v1/cart/discount/", { method: "DELETE", guestCart: true });
}
