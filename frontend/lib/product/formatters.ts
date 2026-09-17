import type { ProductAvailability, ProductPricing } from "./types";

/**
 * Deterministic number formatter using ASCII digits with thousand separators.
 * Unlike toLocaleString("fa-IR"), this produces identical output on both
 * Node.js (SSR) and the browser, preventing React hydration mismatches.
 */
export function formatNumber(value: number): string {
  const [intPart, decPart] = value.toFixed(0).split(".");
  const withSeparators = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return decPart != null ? `${withSeparators}.${decPart}` : withSeparators;
}

export const formatProductMoney = (value?: string | null, locale = "fa") => {
  if (value == null || value === "") return locale === "en" ? "Not listed" : "ثبت نشده";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return locale === "en" ? "Not listed" : "ثبت نشده";
  return formatNumber(numeric);
};
export const isAvailable = (availability: ProductAvailability) => availability.availableToCart > 0;
export const hasDiscount = (pricing?: ProductPricing) => Number(pricing?.discountPercentage ?? 0) > 0;
