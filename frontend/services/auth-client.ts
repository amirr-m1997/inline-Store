export type Customer = { id: number; first_name: string; last_name: string; email: string | null; phone_number: string | null; landline: string; customer_type: "personal" | "business"; company_name: string; national_id: string; economic_code: string; job_title: string; province: string; city: string; postal_code: string; address: string; date_joined: string };
import { getCart } from "../lib/api/cart";

export async function mergeGuestCart() {
  if (!localStorage.getItem("guestCartToken")) return;
  try { await getCart(); window.dispatchEvent(new Event("cart-updated")); } catch { /* Preserve the existing silent merge failure. */ }
}

export function authChanged(authenticated = true) { window.dispatchEvent(new CustomEvent("auth-changed", { detail: { authenticated } })); }

export async function parseError(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (data && typeof data === "object" && typeof (data as { detail?: unknown }).detail === "string") return (data as { detail: string }).detail;
  const flatten = (value: unknown): string[] => {
    if (typeof value === "string") return [value];
    if (typeof value === "number" || typeof value === "boolean") return [String(value)];
    if (Array.isArray(value)) return value.flatMap(flatten);
    if (value && typeof value === "object") return Object.values(value).flatMap(flatten);
    return [];
  };
  const english = typeof window !== "undefined" && window.location.pathname.startsWith("/en");
  return flatten(data).join(" ") || (english ? "Request failed." : "درخواست ناموفق بود.");
}
