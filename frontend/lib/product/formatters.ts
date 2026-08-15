import type { ProductAvailability, ProductPricing } from "./types";
export const formatProductMoney = (value?: string) => value ? Number(value).toLocaleString("fa-IR", { maximumFractionDigits: 0 }) : "ثبت نشده";
export const isAvailable = (availability: ProductAvailability) => availability.availableToCart > 0;
export const hasDiscount = (pricing?: ProductPricing) => Number(pricing?.discountPercentage ?? 0) > 0;
