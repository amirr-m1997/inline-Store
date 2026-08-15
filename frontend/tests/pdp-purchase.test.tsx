import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { VariantSelector } from "../components/product/detail/variant-selector";
import { clampPurchaseQuantity, getMissingVariantAttributes, getPurchaseCtaState } from "../components/product/detail/product-detail-interactive";
import type { ProductDetail } from "../lib/product/types";

const product = { id: 1, name: "محصول", slug: "product", code: "P-1", unit: "عدد", media: [], availability: { quantity: 4, availableToCart: 4 }, categories: [], specifications: [], variants: [{ id: "v1", sku: "V-RED", attributes: [{ name: "رنگ", value: "قرمز" }, { name: "سایز", value: "متوسط" }] }, { id: "v2", sku: "V-BLUE", attributes: [{ name: "رنگ", value: "آبی" }, { name: "سایز", value: "بزرگ" }] }], serviceAdvantages: [], relationships: [], documents: [] } as ProductDetail;

describe("PDP purchase and variant UX", () => {
  it("identifies incomplete variant attributes", () => {
    expect(getMissingVariantAttributes(product.variants, { رنگ: "قرمز" })).toEqual(["سایز"]);
    expect(getMissingVariantAttributes(product.variants, { رنگ: "قرمز", سایز: "متوسط" })).toEqual([]);
  });

  it("clamps quantity to the real inventory limit", () => {
    expect(clampPurchaseQuantity(0, 4)).toBe(1);
    expect(clampPurchaseQuantity(9, 4)).toBe(4);
    expect(clampPurchaseQuantity(Number.NaN, 0)).toBe(0);
  });

  it.each([[false, false, 4, false, "ready"], [true, false, 0, false, "selection_required"], [true, true, 0, false, "unavailable"], [true, true, 2, true, "loading"]] as const)("exposes CTA state %s", (hasVariants, selected, available, adding, expected) => {
    expect(getPurchaseCtaState(hasVariants, selected, available, adding)).toBe(expected);
  });

  it("marks combinations unavailable without relying only on color", () => {
    const onChange = vi.fn();
    render(<VariantSelector product={product} onChange={onChange} />);
    const color = screen.getByRole("button", { name: "قرمز" });
    fireEvent.click(color);
    fireEvent.click(screen.getByRole("button", { name: "متوسط" }));
    expect(screen.getByRole("button", { name: /آبی/ })).toBeDisabled();
    expect(onChange).toHaveBeenCalled();
  });
});
