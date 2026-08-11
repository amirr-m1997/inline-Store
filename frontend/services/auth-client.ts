export type Customer = { id: number; first_name: string; last_name: string; email: string | null; phone_number: string | null; landline: string; customer_type: "personal" | "business"; company_name: string; national_id: string; economic_code: string; job_title: string; province: string; city: string; postal_code: string; address: string; date_joined: string };

export async function mergeGuestCart() {
  const guestToken = localStorage.getItem("guestCartToken");
  if (!guestToken) return;
  const response = await fetch("/api/v1/cart/", { headers: { "X-Guest-Token": guestToken }, cache: "no-store" });
  if (response.ok) { const cart = await response.json(); if (!cart.guest_token) localStorage.removeItem("guestCartToken"); window.dispatchEvent(new Event("cart-updated")); }
}

export function authChanged() { window.dispatchEvent(new Event("auth-changed")); }

export async function parseError(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (typeof data.detail === "string") return data.detail;
  return Object.values(data).flat().join(" ") || "درخواست ناموفق بود.";
}
