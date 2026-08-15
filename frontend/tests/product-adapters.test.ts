import { describe, expect, it } from "vitest";
import { toProductSummary, toProductDetail } from "../lib/product/adapters";

const raw = { id: 3, name: "کابل", slug: "cable", code: "C-3", unit: "عدد", available_quantity: 4, category: { name_fa: "کابل" }, images: [{ image: "/cable.jpg", alt_text: "Cable", alt_fa: "کابل", is_primary: true }], price: { original_amount: "100", final_amount: "80", discount_percentage: "20" } };

describe("product adapters", () => {
  it("preserves catalog identity, media, pricing and availability", () => {
    expect(toProductSummary(raw)).toMatchObject({ id: 3, name: "کابل", code: "C-3", pricing: { finalAmount: "80" }, availability: { quantity: 4 } });
  });
  it("maps detail domain fields", () => {
    const detail = toProductDetail({ ...raw, name_fa: raw.name, sku: raw.code, name_en: "Cable", description: "desc", inventory: { allowed_for_cart: 2 }, pricing: { price: "100", final_price: "80", discount_percentage: "20" }, category_tree: [{ id: 1, name_fa: "کابل", slug: "cable" }], technical_specifications: [], service_advantages: [], related_products: [], images: [{ url: "/cable.jpg", alt_text: "Cable", alt_fa: "کابل" }] });
    expect(detail).toMatchObject({ sku: "C-3", nameEn: "Cable", categories: [{ slug: "cable" }] });
  });
});
