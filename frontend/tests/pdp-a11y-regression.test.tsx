import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProductIdentity } from "../components/product/detail/product-identity";
import type { ProductDetail } from "../lib/product/types";

const product: ProductDetail = {
  id: 1,
  name: "محصول تست",
  slug: "test-product",
  code: "T-1",
  unit: "عدد",
  sku: "T-1",
  nameEn: "Test Product",
  description: "",
  categories: [{ id: 1, name: "کابل", slug: "cable" }],
  media: [],
  pricing: undefined,
  availability: { quantity: 4, availableToCart: 4 },
  specifications: [],
  serviceAdvantages: [],
  variants: [],
  relationships: [],
  documents: [],
};

describe("PDP accessibility regressions", () => {
  it("renders the real product title as exactly one H1", () => {
    render(<ProductIdentity product={product} />);
    expect(screen.getAllByRole("heading", { level: 1, name: product.name })).toHaveLength(1);
  });
});
