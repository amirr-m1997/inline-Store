export type Customer = { id: number; first_name: string; last_name: string; email: string | null; phone_number: string | null; landline: string; customer_type: "personal" | "business"; company_name: string; national_id: string; economic_code: string; job_title: string; province: string; city: string; postal_code: string; address: string; date_joined: string };
import { getCart } from "../lib/api/cart";

export async function mergeGuestCart() {
  if (!localStorage.getItem("guestCartToken")) return;
  try { await getCart(); window.dispatchEvent(new Event("cart-updated")); } catch { /* Preserve the existing silent merge failure. */ }
}

export function authChanged() { window.dispatchEvent(new Event("auth-changed")); }

export async function parseError(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (typeof data.detail === "string") return data.detail;
  return Object.values(data).flat().join(" ") || "درخواست ناموفق بود.";
}
