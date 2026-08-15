import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProductCard } from "../components/catalog/product-card";
import { VariantSelector } from "../components/product/detail/variant-selector";
import { groupSpecifications } from "../components/product/detail/product-specifications";
import { mapFacets } from "../components/catalog/catalog-explorer";
import type { ProductDetail } from "../lib/product/types";

const product = { id: 1, name: "محصول تست", slug: "test", code: "T-1", unit: "عدد", available_quantity: 2, category: null, images: [], price: null };
const detail = { id: 1, name: "محصول", slug: "p", code: "P", unit: "عدد", media: [], availability: { quantity: 1, availableToCart: 1 }, categories: [], specifications: [{ label: "ولتاژ", value: "220", group: "برق", unit: "V" }], variants: [{ id: "v1", sku: "V1", attributes: [{ name: "رنگ", value: "قرمز" }] }, { id: "v2", sku: "V2", attributes: [{ name: "رنگ", value: "آبی" }] }], serviceAdvantages: [], relationships: [], documents: [] } as ProductDetail;

describe("catalog and product components", () => {
  it("maps hierarchical facets to the existing category facet type", () => {
    expect(mapFacets([{ name: "category", type: "hierarchical_category", options: [] }])).toEqual([{ name: "category", type: "category", options: [] }]);
  });
  it("renders a product card", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByText("محصول تست")).toBeInTheDocument();
  });
  it("selects a variant with an accessible pressed control", () => {
    const onChange = vi.fn();
    render(<VariantSelector product={detail} onChange={onChange} />);
    const button = screen.getByRole("button", { name: "قرمز" });
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ selected: { "رنگ": "قرمز" } }));
  });
  it("groups specifications by their backend group", () => {
    expect(groupSpecifications(detail)).toEqual([{ name: "برق", attributes: [{ name: "ولتاژ", value: "220", unit: "V" }] }]);
  });
});
