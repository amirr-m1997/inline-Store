import type { ProductAvailability, ProductPricing } from "./types";
export const formatProductMoney = (value?: string | null, locale = "fa") => {
  if (value == null || value === "") return locale === "en" ? "Not listed" : "ثبت نشده";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return locale === "en" ? "Not listed" : "ثبت نشده";
  return numeric.toLocaleString(locale === "en" ? "en-US" : "fa-IR", { maximumFractionDigits: 0 });
};
export const isAvailable = (availability: ProductAvailability) => availability.availableToCart > 0;
export const hasDiscount = (pricing?: ProductPricing) => Number(pricing?.discountPercentage ?? 0) > 0;
